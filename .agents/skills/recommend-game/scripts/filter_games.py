"""
Query-Based Game Filter with Boolean Logic

Filters database/library.json using boolean filter expressions.

Syntax:
  genre:RPG AND tag:Co-op OR feature:"Full Controller Support"
  NOT genre:Horror
  timeEarned:[0.0-100.0] (for time_played_hours range)
  score:[75-90] (for community_score range)
  criticScore:[70-100] (for critic_score range)

Operators:
  AND (higher precedence), OR, NOT

Returns: JSON array of all matching games
"""

import json
import argparse
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
LIBRARY_PATH = DB_DIR / "library.json"
PROFILE_PATH = DB_DIR / "user_profile.json"


class Token:
    """Represent a token in the filter expression."""
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class Tokenizer:
    """Tokenize filter expressions."""
    
    def __init__(self, expression):
        self.expression = expression
        self.pos = 0
        self.tokens = []
    
    def tokenize(self):
        """Tokenize the expression into a list of tokens."""
        while self.pos < len(self.expression):
            # Skip whitespace
            if self.expression[self.pos].isspace():
                self.pos += 1
                continue
            
            # Operators
            if self.expression[self.pos:self.pos+3] == "AND":
                self.tokens.append(Token("AND", "AND"))
                self.pos += 3
            elif self.expression[self.pos:self.pos+2] == "OR":
                self.tokens.append(Token("OR", "OR"))
                self.pos += 2
            elif self.expression[self.pos:self.pos+3] == "NOT":
                self.tokens.append(Token("NOT", "NOT"))
                self.pos += 3
            elif self.expression[self.pos] == "(":
                self.tokens.append(Token("LPAREN", "("))
                self.pos += 1
            elif self.expression[self.pos] == ")":
                self.tokens.append(Token("RPAREN", ")"))
                self.pos += 1
            
            # Quoted string
            elif self.expression[self.pos] == '"':
                self.pos += 1
                start = self.pos
                while self.pos < len(self.expression) and self.expression[self.pos] != '"':
                    self.pos += 1
                value = self.expression[start:self.pos]
                if self.pos < len(self.expression):
                    self.pos += 1  # skip closing quote
                self.tokens.append(Token("VALUE", value))
            
            # Field:value or range syntax
            elif ":" in self.expression[self.pos:]:
                # Find the next space, paren, or operator
                start = self.pos
                while (self.pos < len(self.expression) and 
                       not self.expression[self.pos].isspace() and 
                       self.expression[self.pos] not in "()"):
                    self.pos += 1
                token_str = self.expression[start:self.pos]
                self.tokens.append(Token("FIELD_EXPR", token_str))
            
            # Bare identifier (shouldn't normally happen, but handle gracefully)
            else:
                start = self.pos
                while (self.pos < len(self.expression) and 
                       not self.expression[self.pos].isspace() and 
                       self.expression[self.pos] not in "()"):
                    self.pos += 1
                token_str = self.expression[start:self.pos]
                self.tokens.append(Token("IDENTIFIER", token_str))
        
        return self.tokens


class Parser:
    """Parse tokenized filter expressions into an AST."""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self):
        """Parse the tokens and return an AST."""
        if not self.tokens:
            return None
        return self.parse_or()
    
    def parse_or(self):
        """Parse OR expressions (lowest precedence)."""
        left = self.parse_and()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].type == "OR":
            self.pos += 1  # skip OR
            right = self.parse_and()
            left = ("OR", left, right)
        
        return left
    
    def parse_and(self):
        """Parse AND expressions (higher precedence)."""
        left = self.parse_not()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].type == "AND":
            self.pos += 1  # skip AND
            right = self.parse_not()
            left = ("AND", left, right)
        
        return left
    
    def parse_not(self):
        """Parse NOT expressions and primary expressions."""
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == "NOT":
            self.pos += 1  # skip NOT
            expr = self.parse_primary()
            return ("NOT", expr)
        
        return self.parse_primary()
    
    def parse_primary(self):
        """Parse primary expressions (parentheses or field:value)."""
        if self.pos >= len(self.tokens):
            return None
        
        token = self.tokens[self.pos]
        
        if token.type == "LPAREN":
            self.pos += 1  # skip (
            expr = self.parse_or()
            if self.pos < len(self.tokens) and self.tokens[self.pos].type == "RPAREN":
                self.pos += 1  # skip )
            return expr
        
        elif token.type == "FIELD_EXPR":
            self.pos += 1
            return ("FIELD", token.value)
        
        else:
            # Unexpected token, skip it
            self.pos += 1
            return None


def parse_field_expression(expr_str):
    """Parse a field:value or field:[range] expression."""
    # Split on colon
    if ":" not in expr_str:
        return None, None, None
    
    field, _, value = expr_str.partition(":")
    field = field.strip()
    value = value.strip()
    
    # Check for range syntax [min-max]
    range_match = re.match(r'\[([-\d.]+)-([-\d.]+)\]', value)
    if range_match:
        try:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            return field, "range", (min_val, max_val)
        except (ValueError, AttributeError):
            return field, "literal", value
    
    return field, "literal", value


def matches_game(game, ast):
    """Evaluate AST against a game object."""
    if ast is None:
        return True
    
    if isinstance(ast, tuple):
        op = ast[0]
        
        if op == "OR":
            left_match = matches_game(game, ast[1])
            right_match = matches_game(game, ast[2])
            return left_match or right_match
        
        elif op == "AND":
            left_match = matches_game(game, ast[1])
            right_match = matches_game(game, ast[2])
            return left_match and right_match
        
        elif op == "NOT":
            expr_match = matches_game(game, ast[1])
            return not expr_match
        
        elif op == "FIELD":
            field_expr = ast[1]
            field, expr_type, value = parse_field_expression(field_expr)
            
            if field is None:
                return False
            
            # Map field aliases to game properties
            field_map = {
                "genre": "genres",
                "tag": "tags",
                "feature": "features",
                "source": "sources",
                "timeEarned": "time_played_hours",
                "score": "community_score",
                "criticScore": "critic_score",
            }
            
            game_field = field_map.get(field, field)
            
            if expr_type == "literal":
                game_value = game.get(game_field)
                
                # For array fields, check if value is in the array
                if isinstance(game_value, list):
                    return value.lower() in [v.lower() for v in game_value]
                
                # For string fields, case-insensitive comparison
                elif isinstance(game_value, str):
                    return value.lower() in game_value.lower()
                
                return False
            
            elif expr_type == "range":
                min_val, max_val = value
                game_value = game.get(game_field)
                
                if game_value is None:
                    return False
                
                try:
                    game_val_float = float(game_value)
                    return min_val <= game_val_float <= max_val
                except (ValueError, TypeError):
                    return False
            
            return False
    
    return True


def load_library():
    """Load library.json."""
    if not LIBRARY_PATH.exists():
        print(f"Error: {LIBRARY_PATH} not found.")
        raise SystemExit(1)
    
    try:
        with LIBRARY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                print("Error: library.json should be an array of game objects.")
                raise SystemExit(1)
            return data
    except json.JSONDecodeError as e:
        print(f"Error reading library.json: {e}")
        raise SystemExit(1)


def load_profile():
    """Load user profile if available."""
    if not PROFILE_PATH.exists():
        return None
    
    try:
        with PROFILE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def filter_games(games, query_str, output_fields=None, sort_by=None, limit=None):
    """Filter games based on query expression."""
    
    # Tokenize and parse the query
    tokenizer = Tokenizer(query_str)
    tokens = tokenizer.tokenize()
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    if ast is None:
        print("Error: Invalid query expression.")
        raise SystemExit(1)
    
    # Filter games
    matching_games = []
    for game in games:
        if matches_game(game, ast):
            matching_games.append(game)
    
    # Sort if requested
    if sort_by:
        try:
            reverse = sort_by.startswith("-")
            field = sort_by.lstrip("-")
            matching_games.sort(
                key=lambda g: (g.get(field) is None, g.get(field)),
                reverse=reverse
            )
        except Exception as e:
            print(f"Warning: Could not sort by {sort_by}: {e}")
    
    # Limit if requested
    if limit:
        matching_games = matching_games[:limit]
    
    # Select output fields if specified
    if output_fields:
        fields = [f.strip() for f in output_fields.split(",")]
        matching_games = [
            {k: v for k, v in game.items() if k in fields}
            for game in matching_games
        ]
    
    return matching_games


def main():
    parser = argparse.ArgumentParser(
        description="Filter games from library.json using boolean filter expressions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python filter_games.py --query "genre:RPG AND tag:Co-op"
  python filter_games.py --query "NOT genre:Horror OR feature:'Full Controller Support'"
  python filter_games.py --query "timeEarned:[50.0-200.0]" --sort-by "-time_played_hours"
  python filter_games.py --query "score:[75-90]" --limit 5
        """
    )
    
    parser.add_argument(
        "--query",
        required=True,
        help="Boolean filter expression (e.g., 'genre:RPG AND tag:Co-op')"
    )
    parser.add_argument(
        "--profile-file",
        help="Path to user profile JSON (for future enhancements)"
    )
    parser.add_argument(
        "--output-fields",
        help="Comma-separated list of fields to include in output"
    )
    parser.add_argument(
        "--sort-by",
        help="Field to sort by (prefix with '-' for descending)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of results to return"
    )
    
    args = parser.parse_args()
    
    # Load library
    games = load_library()
    
    # Filter
    try:
        results = filter_games(
            games,
            args.query,
            output_fields=args.output_fields,
            sort_by=args.sort_by,
            limit=args.limit
        )
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)
    
    # Output JSON
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
