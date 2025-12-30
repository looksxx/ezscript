import sys
import re
import time
import random
import json
import ctypes
import tkinter as tk
from pathlib import Path
from tkinter import Canvas
from PIL import Image, ImageTk
from datetime import datetime

variables = {}
functions = {}
key_states = {}

# Configure comment styles (you can change these!)
COMMENT_STYLES = ['#']
# Global window variables
window = None
canvas = None
window_objects = []

def _set_default_icon():
    if window:
        try:
            script_dir = Path(__file__).parent
            default_icon = script_dir / "icon.ico"
            if default_icon.exists():
                window.iconbitmap(str(default_icon))
        except:
            pass

# Windows-only: disable maximize button
def _disable_maximize():
    if sys.platform.startswith("win"):
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        GWL_STYLE = -16
        WS_MAXIMIZEBOX = 0x00010000
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        style = style & ~WS_MAXIMIZEBOX
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            0x0002 | 0x0001 | 0x0020  # SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED
        )

def _create_window(width, height, title,
                   resizable=False, always_on_top=False, can_maximize=True):
    global window, canvas, window_objects
    window = tk.Tk()
    window.title(title)
    canvas = Canvas(window, width=width, height=height, bg="white")
    canvas.pack()
    window_objects = []

    # Window properties
    window.resizable(resizable, resizable)
    window.attributes("-topmost", always_on_top)

    # Set default icon
    _set_default_icon()

    # Disable maximize button if needed (Windows only)
    if not can_maximize:
        window.after_idle(_disable_maximize)


def _set_window_title(title):
    if window:
        window.title(title)
    return title

def _set_window_size(width, height):
    if window:
        window.geometry(f"{width}x{height}")
    return f"{width}x{height}"

def _set_background(color):
    if canvas:
        canvas.config(bg=color)
    return color

def _draw_circle(x, y, radius, color, fill):
    if canvas:
        obj = canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                 outline=color, fill=fill if fill else "")
        window_objects.append(obj)
        return obj
    return None

def _draw_rectangle(x1, y1, x2, y2, color, fill):
    if canvas:
        obj = canvas.create_rectangle(x1, y1, x2, y2, 
                                       outline=color, fill=fill if fill else "")
        window_objects.append(obj)
        return obj
    return None

def _draw_line(x1, y1, x2, y2, color, width):
    if canvas:
        obj = canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        window_objects.append(obj)
        return obj
    return None

def _draw_text(x, y, text, color, font_size):
    if canvas:
        obj = canvas.create_text(x, y, text=text, fill=color, 
                                 font=("Arial", font_size))
        window_objects.append(obj)
        return obj
    return None

def _load_image(path, x, y, width=None, height=None):
    if canvas:
        try:
            img = Image.open(path)
            if width is not None and height is not None:
                img = img.resize((width, height), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            obj = canvas.create_image(x, y, image=photo, anchor=tk.NW)

            if not hasattr(canvas, 'images'):
                canvas.images = []
            canvas.images.append(photo)

            window_objects.append(obj)
            return obj
        except Exception as e:
            raise EzScriptError(f"Cannot load image: {e}")
    return None

def _clear_window():
    if canvas:
        canvas.delete("all")
        window_objects.clear()
    return "Cleared"

def _update_window():
    if window:
        window.update()
    return "Updated"

def _show_window():
    if window:
        window.mainloop()
    return "Window shown"

def _close_window():
    if window:
        window.destroy()
    return "Window closed"
def _set_window_icon(icon_path):
    if window:
        try:
            # Try .ico format first
            if icon_path.endswith('.ico'):
                window.iconbitmap(icon_path)
            else:
                # For PNG, JPG, etc.
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                window.iconphoto(True, photo)
                # Keep reference to prevent garbage collection
                if not hasattr(window, 'icon_image'):
                    window.icon_image = photo
                else:
                    window.icon_image = photo
            return "Icon set"
        except Exception as e:
            raise EzScriptError(f"Cannot set icon: {e}")
    return None

def _remove_window_icon():
    if window:
        try:
            # Set to blank/default icon
            window.iconbitmap('')
            return "Icon removed"
        except:
            pass
    return None

# ==========================
# API wrappers for EzScript
# ==========================

def _api_onKeyDown(*args):
    if len(args) != 2:
        raise EzScriptError("onKeyDown(key, callback) expects 2 arguments")
    key, callback = args
    if not isinstance(key, str):
        raise EzScriptError("onKeyDown: key must be a string")
    if not callable(callback):
        raise EzScriptError("onKeyDown: callback must be a function")

    def handler(event):
        key_states[key] = True
        callback()

    if window:
        window.bind(f"<KeyPress-{key}>", lambda e: handler(e))
    return "Callback registered"

def _api_onKeyUp(*args):
    if len(args) != 2:
        raise EzScriptError("onKeyUp(key, callback) expects 2 arguments")
    key, callback = args
    if not isinstance(key, str):
        raise EzScriptError("onKeyUp: key must be a string")
    if not callable(callback):
        raise EzScriptError("onKeyUp: callback must be a function")

    def handler(event):
        key_states[key] = False
        callback()

    if window:
        window.bind(f"<KeyRelease-{key}>", lambda e: handler(e))
    return "Callback registered"

def _api_createWindow(*args):
    if len(args) < 3 or len(args) > 6:
        raise EzScriptError("createWindow(width, height, title, resizable?, alwaysOnTop?, canMaximize?) expects 3–6 arguments")

    width, height, title = args[0], args[1], args[2]
    resizable = args[3] if len(args) >= 4 else False
    always_on_top = args[4] if len(args) >= 5 else False
    can_maximize = args[5] if len(args) == 6 else False

    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise EzScriptError("createWindow: width and height must be numbers")
    if not isinstance(title, str):
        raise EzScriptError("createWindow: title must be a string")
    if not isinstance(resizable, bool):
        raise EzScriptError("createWindow: resizable must be true or false")
    if not isinstance(always_on_top, bool):
        raise EzScriptError("createWindow: alwaysOnTop must be true or false")
    if not isinstance(can_maximize, bool):
        raise EzScriptError("createWindow: canMaximize must be true or false")

    return _create_window(width, height, title, resizable, always_on_top, can_maximize)



def _api_setWindowTitle(*args):
    if len(args) != 1:
        raise EzScriptError("setWindowTitle(title) expects 1 argument")
    if not isinstance(args[0], str):
        raise EzScriptError("setWindowTitle: title must be a string")
    return _set_window_title(args[0])


def _api_setWindowSize(*args):
    if len(args) != 2:
        raise EzScriptError("setWindowSize(width, height) expects 2 arguments")
    width, height = args
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise EzScriptError("setWindowSize: width and height must be numbers")
    return _set_window_size(width, height)


def _api_setBackground(*args):
    if len(args) != 1:
        raise EzScriptError("setBackground(color) expects 1 argument")
    if not isinstance(args[0], str):
        raise EzScriptError("setBackground: color must be a string")
    return _set_background(args[0])


def _api_drawCircle(*args):
    if len(args) < 3 or len(args) > 5:
        raise EzScriptError("drawCircle(x, y, radius, color?, fill?) expects 3–5 arguments")
    x, y, radius = args[0], args[1], args[2]
    color = args[3] if len(args) >= 4 else "black"
    fill = args[4] if len(args) == 5 else None

    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not isinstance(radius, (int, float)):
        raise EzScriptError("drawCircle: x, y, radius must be numbers")
    if not isinstance(color, str):
        raise EzScriptError("drawCircle: color must be a string")
    if fill is not None and not isinstance(fill, str):
        raise EzScriptError("drawCircle: fill must be a string or None")
    return _draw_circle(x, y, radius, color, fill)


def _api_drawRectangle(*args):
    if len(args) < 4 or len(args) > 6:
        raise EzScriptError("drawRectangle(x1, y1, x2, y2, color?, fill?) expects 4–6 arguments")
    x1, y1, x2, y2 = args[0], args[1], args[2], args[3]
    color = args[4] if len(args) >= 5 else "black"
    fill = args[5] if len(args) == 6 else None

    if not all(isinstance(v, (int, float)) for v in [x1, y1, x2, y2]):
        raise EzScriptError("drawRectangle: x1, y1, x2, y2 must be numbers")
    if not isinstance(color, str):
        raise EzScriptError("drawRectangle: color must be a string")
    if fill is not None and not isinstance(fill, str):
        raise EzScriptError("drawRectangle: fill must be a string or None")
    return _draw_rectangle(x1, y1, x2, y2, color, fill)


def _api_drawLine(*args):
    if len(args) < 4 or len(args) > 6:
        raise EzScriptError("drawLine(x1, y1, x2, y2, color?, width?) expects 4–6 arguments")
    x1, y1, x2, y2 = args[0], args[1], args[2], args[3]
    color = args[4] if len(args) >= 5 else "black"
    width = args[5] if len(args) == 6 else 1

    if not all(isinstance(v, (int, float)) for v in [x1, y1, x2, y2]):
        raise EzScriptError("drawLine: x1, y1, x2, y2 must be numbers")
    if not isinstance(color, str):
        raise EzScriptError("drawLine: color must be a string")
    if not isinstance(width, (int, float)):
        raise EzScriptError("drawLine: width must be a number")
    return _draw_line(x1, y1, x2, y2, color, width)


def _api_drawText(*args):
    if len(args) < 3 or len(args) > 5:
        raise EzScriptError("drawText(x, y, text, color?, fontSize?) expects 3–5 arguments")
    
    x, y, text = args[0], args[1], args[2]
    color = args[3] if len(args) >= 4 else "black"
    fontSize = args[4] if len(args) == 5 else 12

    if not all(isinstance(v, (int, float)) for v in [x, y]):
        raise EzScriptError("drawText: x and y must be numbers")
    if not isinstance(text, str):
        raise EzScriptError("drawText: text must be a string")
    if not isinstance(color, str):
        raise EzScriptError("drawText: color must be a string")
    if not isinstance(fontSize, (int, float)):
        raise EzScriptError("drawText: fontSize must be a number")

    return _draw_text(x, y, text, color, fontSize)


def _api_loadImage(*args):
    if len(args) < 3 or len(args) > 5:
        raise EzScriptError("loadImage(path, x, y, width?, height?) expects 3–5 arguments")
    path, x, y = args[0], args[1], args[2]
    width = args[3] if len(args) >= 4 else None
    height = args[4] if len(args) == 5 else None

    if not isinstance(path, str):
        raise EzScriptError("loadImage: path must be a string")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise EzScriptError("loadImage: x and y must be numbers")
    if width is not None and not isinstance(width, (int, float)):
        raise EzScriptError("loadImage: width must be a number or None")
    if height is not None and not isinstance(height, (int, float)):
        raise EzScriptError("loadImage: height must be a number or None")

    return _load_image(path, x, y, width, height)


def _api_clearWindow(*args):
    if len(args) != 0:
        raise EzScriptError("clearWindow() expects 0 arguments")
    return _clear_window()


def _api_updateWindow(*args):
    if len(args) != 0:
        raise EzScriptError("updateWindow() expects 0 arguments")
    return _update_window()


def _api_showWindow(*args):
    if len(args) != 0:
        raise EzScriptError("showWindow() expects 0 arguments")
    return _show_window()


def _api_closeWindow(*args):
    if len(args) != 0:
        raise EzScriptError("closeWindow() expects 0 arguments")
    return _close_window()


def _api_setWindowIcon(*args):
    if len(args) != 1:
        raise EzScriptError("setWindowIcon(path) expects 1 argument")
    path = args[0]
    if not isinstance(path, str):
        raise EzScriptError("setWindowIcon: path must be a string")
    return _set_window_icon(path)


def _api_removeWindowIcon(*args):
    if len(args) != 0:
        raise EzScriptError("removeWindowIcon() expects 0 arguments")
    return _remove_window_icon()

class Return(Exception):
    def __init__(self, value):
        self.value = value

class Break(Exception):
    pass

class Continue(Exception):
    pass

class EzScriptError(Exception):
    """Custom exception for EzScript runtime errors"""
    def __init__(self, message, line_number=None):
        self.message = message
        self.line_number = line_number
        super().__init__(self.message)

def is_comment(line):
    """Check if a line is a comment based on configured styles."""
    stripped = line.strip()
    for style in COMMENT_STYLES:
        if stripped.startswith(style):
            return True
    return False

def strip_inline_comment(line):
    """Remove inline comments from a line, being careful about strings."""
    result = ""
    in_string = False
    string_char = None
    i = 0
    
    while i < len(line):
        char = line[i]
        
        # Handle string boundaries
        if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            result += char
            i += 1
            continue
        
        # If we're in a string, just add the character
        if in_string:
            result += char
            i += 1
            continue
        
        # Check for comment markers outside of strings
        for comment_style in COMMENT_STYLES:
            if line[i:i+len(comment_style)] == comment_style:
                # Found a comment, return everything before it
                return result.rstrip()
        
        result += char
        i += 1
    
    return result

def eval_expr(expr, line_num=None):
    """Evaluate an expression using current variables and built-in functions."""
    expr = expr.strip()
    try:
        return int(expr)
    except ValueError:
        pass
    try:
        return float(expr)
    except ValueError:
        pass
    
    # Handle string interpolation with {} BEFORE checking for string literals
    if (expr.startswith('"') or expr.startswith("'")) and '{' in expr and '}' in expr:
        # Extract the string content
        quote_char = expr[0]
        string_content = expr[1:-1] if expr.endswith(quote_char) else expr[1:]
        
        # Replace variables in the string
        result = string_content
        for var_name, var_value in variables.items():
            result = result.replace(f'{{{var_name}}}', str(var_value))
        
        # Process escape sequences
        result = result.replace('\\n', '\n')
        result = result.replace('\\t', '\t')
        result = result.replace('\\r', '\r')
        result = result.replace('\\\\', '\\')
        
        return result
    
    # Handle string literals with escape sequences
    if (expr.startswith('"') and expr.endswith('"')) or \
       (expr.startswith("'") and expr.endswith("'")):
        string_content = expr[1:-1]
        # Process escape sequences
        string_content = string_content.replace('\\n', '\n')
        string_content = string_content.replace('\\t', '\t')
        string_content = string_content.replace('\\r', '\r')
        string_content = string_content.replace('\\\\', '\\')
        return string_content
    
    # --- INSERT DICTIONARY HANDLING HERE ---
    # Handle dictionary literals {key: value, ...}
    if expr.startswith("{") and expr.endswith("}"):
        dict_content = expr[1:-1].strip()
        if not dict_content:
            return {}

        result_dict = {}
        parts = []
        current = ""
        depth = 0
        in_string = False
        string_char = None

        for char in dict_content:
            if char in ('"', "'") and (not in_string or char == string_char):
                in_string = not in_string
                string_char = char if in_string else None
                current += char
            elif not in_string:
                if char in "({[":
                    depth += 1
                    current += char
                elif char in ")}]":
                    depth -= 1
                    current += char
                elif char == "," and depth == 0:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
            else:
                current += char
        if current.strip():
            parts.append(current.strip())

        # Split key:value for each part
        for part in parts:
            if ":" not in part:
                raise EzScriptError(f"Invalid dictionary item: {part}", line_num)
            k, v = part.split(":", 1)
            key = eval_expr(k.strip(), line_num)
            value = eval_expr(v.strip(), line_num)
            result_dict[key] = value
        return result_dict

    # Replace natural language operators with Python operators
    expr = expr.replace(" is equal to ", " == ")
    expr = expr.replace(" greater or equal to ", " >= ")
    expr = expr.replace(" lesser or equal to ", " <= ")
    expr = expr.replace(" greater than ", " > ")
    expr = expr.replace(" less than ", " < ")
    expr = expr.replace(" not equal to ", " != ")
    expr = expr.replace(" is not ", " != ")
    expr = expr.replace(" is ", " == ")
    expr = expr.replace(" true", " True")
    expr = expr.replace(" false", " False")
    if expr == "true":
        return True
    if expr == "false":
        return False
    
    # Built-in functions
    builtins = {
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'abs': abs,
        'max': max,
        'min': min,
        'sum': sum,
        'round': round,
        'range': range,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'type': type,
        'sorted': sorted,
        'reversed': reversed,
        'enumerate': enumerate,
        'zip': zip,
        'all': all,
        'any': any,
        'input': input,
        'random': random.randint,
        'choice': random.choice,
        'shuffle': random.shuffle,
        'randrange': random.randrange,
        'uniform': random.uniform,
        'current_time': lambda: datetime.now().strftime("%H:%M:%S"),
        'current_date': lambda: datetime.now().strftime("%Y-%m-%d"),
        'current_datetime': lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'timestamp': lambda: int(datetime.now().timestamp()),
        'createWindow': _api_createWindow,
        'setWindowTitle': _api_setWindowTitle,
        'setWindowSize': _api_setWindowSize,
        'setBackground': _api_setBackground,
        'drawCircle': _api_drawCircle,
        'drawRectangle': _api_drawRectangle,
        'drawLine': _api_drawLine,
        'drawText': _api_drawText,
        'loadImage': _api_loadImage,
        'clearWindow': _api_clearWindow,
        'updateWindow': _api_updateWindow,
        'showWindow': _api_showWindow,
        'closeWindow': _api_closeWindow,
        'setWindowIcon': _api_setWindowIcon,
        'removeWindowIcon': _api_removeWindowIcon,
        'onKeyDown': _api_onKeyDown,
        'onKeyUp': _api_onKeyUp,
        'keyStates': key_states,
    }
    
    try:
        # Combine variables and built-ins for evaluation
        context = {**builtins, **variables, **functions}
        result = eval(expr, {"__builtins__": {}}, context)
        return result
    except NameError as e:
        var_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        raise EzScriptError(f"Variable '{var_name}' is not defined", line_num)
    except ZeroDivisionError:
        raise EzScriptError("Cannot divide by zero", line_num)
    except IndexError as e:
        raise EzScriptError(f"List index out of range: {e}", line_num)
    except KeyError as e:
        raise EzScriptError(f"Dictionary key not found: {e}", line_num)
    except TypeError as e:
        raise EzScriptError(f"Type error: {e}", line_num)
    except SyntaxError as e:
        raise EzScriptError(f"Syntax error in expression: {e}", line_num)
    except EzScriptError:
        # Re-raise EzScriptError without wrapping it
        raise
    except Exception as e:
        # Don't silently return the expression as string - raise the error
        raise EzScriptError(f"Invalid expression: {e}", line_num)

def run_block(lines, start, indent, loop_context=False):
    """Execute a block of code with proper scope handling."""
    i = start
    while i < len(lines):
        line = lines[i]

        # Skip empty lines and comments
        if not line.strip() or is_comment(line):
            i += 1
            continue
        
        # Strip inline comments
        line = strip_inline_comment(line)
        
        # Skip if line became empty after stripping comment
        if not line.strip():
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent < indent:
            return i

        s = line.strip()

        try:
            # Function definition
            if s.startswith("function ") and ("(" in s and ")" in s):
                # Extract function signature
                func_sig = s[9:].strip()
                if func_sig.endswith(":"):
                    func_sig = func_sig[:-1]
                
                # Parse name and parameters
                paren_idx = func_sig.index("(")
                name = func_sig[:paren_idx].strip()
                params_str = func_sig[paren_idx+1:func_sig.rindex(")")]
                
                # Parse parameters with default values
                params = []
                defaults = {}
                if params_str.strip():
                    for param in params_str.split(","):
                        param = param.strip()
                        if "=" in param:
                            param_name, default_val = param.split("=", 1)
                            param_name = param_name.strip()
                            defaults[param_name] = eval_expr(default_val.strip(), i+1)
                            params.append(param_name)
                        else:
                            params.append(param)

                i += 1
                body_start = i
                
                # Find where function block ends
                body_end = i
                func_indent = current_indent
                while body_end < len(lines):
                    l = lines[body_end]
                    if not l.strip() or is_comment(l):
                        body_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= func_indent:
                        break
                    body_end += 1

                def make_func(start, end, params, defaults, func_indent):
                    def fn(*args, **kwargs):
                        backup = variables.copy()
                        
                        # Handle positional arguments
                        for idx, (p, a) in enumerate(zip(params, args)):
                            variables[p] = a
                        
                        # Handle remaining parameters with defaults
                        for idx in range(len(args), len(params)):
                            param = params[idx]
                            if param in kwargs:
                                variables[param] = kwargs[param]
                            elif param in defaults:
                                variables[param] = defaults[param]
                            else:
                                raise EzScriptError(f"Missing required parameter: {param}")
                        
                        try:
                            run_block(lines, start, func_indent + 4)
                            result = None
                        except Return as r:
                            result = r.value
                        variables.clear()
                        variables.update(backup)
                        return result
                    return fn

                functions[name] = make_func(body_start, body_end, params, defaults, current_indent)
                i = body_end
                continue

            # RETURN (can return multiple values)
            if s.startswith("return "):
                expr = s[7:].strip()
                # Check for multiple return values
                if "," in expr:
                    # Parse multiple values carefully
                    parts = []
                    current = ""
                    depth = 0
                    in_string = False
                    string_char = None
                    
                    for char in expr:
                        if char in ('"', "'") and (not in_string or char == string_char):
                            in_string = not in_string
                            string_char = char if in_string else None
                            current += char
                        elif not in_string:
                            if char in '([{':
                                depth += 1
                                current += char
                            elif char in ')]}':
                                depth -= 1
                                current += char
                            elif char == ',' and depth == 0:
                                parts.append(current.strip())
                                current = ""
                            else:
                                current += char
                        else:
                            current += char
                    
                    if current.strip():
                        parts.append(current.strip())
                    
                    values = tuple(eval_expr(part, i+1) for part in parts)
                    raise Return(values)
                else:
                    raise Return(eval_expr(expr, i+1))
            elif s == "return":
                raise Return(None)

            # BREAK
            elif s == "break":
                if not loop_context:
                    raise EzScriptError("'break' can only be used inside a loop", i+1)
                raise Break()

            # CONTINUE
            elif s == "continue":
                if not loop_context:
                    raise EzScriptError("'continue' can only be used inside a loop", i+1)
                raise Continue()

            # THROW (raise an error)
            elif s.startswith("throw "):
                error_msg = eval_expr(s[6:], i+1)
                raise EzScriptError(str(error_msg), i+1)

            # READ FILE (check before general LET assignment)
            elif s.startswith("let ") and " be read file " in s:
                var_name = s[4:s.index(" be read file ")].strip()
                file_expr = s[s.index(" be read file ") + 14:].strip()
                file_path = eval_expr(file_expr, i+1)
                try:
                    with open(file_path, 'r') as f:
                        variables[var_name] = f.read()
                except FileNotFoundError:
                    raise EzScriptError(f"File not found: '{file_path}'", i+1)
                except Exception as e:
                    raise EzScriptError(f"Cannot read file '{file_path}': {e}", i+1)

            # LET assignment (supports multiple variables and unpacking)
            elif s.startswith("let ") and " be " in s:
                parts = s.split(" be ", 1)
                vars_part = parts[0][4:].strip()
                expr_part = parts[1].strip()
                
                # Check if multiple variables
                if "," in vars_part:
                    var_names = [v.strip() for v in vars_part.split(",")]
                    value = eval_expr(expr_part, i+1)
                    
                    # Check if value is iterable (tuple unpacking)
                    try:
                        if isinstance(value, (list, tuple)) and len(value) == len(var_names):
                            for var, val in zip(var_names, value):
                                variables[var] = val
                        else:
                            # Assign same value to all
                            for var in var_names:
                                variables[var] = value
                    except:
                        for var in var_names:
                            variables[var] = value
                else:
                    expr = expr_part
                    if expr.startswith("{") or expr.startswith("["):
                        depth = expr.count("{") + expr.count("[") - expr.count("}") - expr.count("]")
                        while depth > 0:
                            i += 1
                            next_line = lines[i].rstrip()
                            expr += "\n" + next_line
                            depth += next_line.count("{") + next_line.count("[")
                            depth -= next_line.count("}") + next_line.count("]")
                    variables[vars_part] = eval_expr(expr, i+1)

            # Augmented assignment
            elif any(op in s for op in ["+=", "-=", "*=", "/=", "//=", "%=", "**="]):
                for op in ["+=", "-=", "*=", "//=", "/=", "%=", "**="]:
                    if op in s:
                        var, expr = s.split(op, 1)
                        var = var.strip()
                        if var not in variables:
                            raise EzScriptError(f"Variable '{var}' is not defined", i+1)
                        expr_val = eval_expr(expr.strip(), i+1)
                        if op == "+=":
                            variables[var] += expr_val
                        elif op == "-=":
                            variables[var] -= expr_val
                        elif op == "*=":
                            variables[var] *= expr_val
                        elif op == "//=":
                            variables[var] //= expr_val
                        elif op == "/=":
                            variables[var] /= expr_val
                        elif op == "%=":
                            variables[var] %= expr_val
                        elif op == "**=":
                            variables[var] **= expr_val
                        break

            # INPUT
            elif s.startswith("let ") and " be input(" in s:
                # Extract variable and prompt
                var_name = s[4:s.index(" be input(")].strip()
                prompt_start = s.index("input(") + 6
                prompt_end = s.rindex(")")
                prompt = s[prompt_start:prompt_end].strip()
                prompt = eval_expr(prompt, i+1)
                variables[var_name] = input(prompt)

            elif s.startswith("print ") and not s.startswith("print("):
                raise EzScriptError("print requires parentheses: use print(...) instead of print ...", i+1)

            # Print
            elif s.startswith("print("):
                # Extract expression from inside parentheses
                start_paren = s.index("(")
                if not s.endswith(")"):
                    raise EzScriptError(f"Missing closing parenthesis in print statement", i+1)
                expr = s[start_paren+1:-1].strip()
                
                # Check if there are multiple comma-separated expressions
                parts = []
                current = ""
                depth = 0
                in_string = False
                string_char = None
                
                for char in expr:
                    if char in ('"', "'") and (not in_string or char == string_char):
                        in_string = not in_string
                        string_char = char if in_string else None
                        current += char
                    elif not in_string:
                        if char in '([{':
                            depth += 1
                            current += char
                        elif char in ')]}':
                            depth -= 1
                            current += char
                        elif char == ',' and depth == 0:
                            parts.append(current.strip())
                            current = ""
                        else:
                            current += char
                    else:
                        current += char
                
                if current.strip():
                    parts.append(current.strip())
                
                # Evaluate and print all parts
                results = []
                for part in parts:
                    evaluated = eval_expr(part, i+1)
                    # Handle string interpolation if not already done
                    if isinstance(evaluated, str) and '{' in evaluated and '}' in evaluated:
                        for var_name, var_value in variables.items():
                            evaluated = evaluated.replace(f'{{{var_name}}}', str(var_value))
                    results.append(str(evaluated))
                
                print(" ".join(results))

            # Wait/Sleep
            elif s.startswith("wait ") and ("second" in s or "seconds" in s):
                time_expr = s[5:].replace("seconds", "").replace("second", "").strip()
                wait_time = float(eval_expr(time_expr, i+1))
                time.sleep(wait_time)

            # WRITE FILE
            elif s.startswith("write ") and " to file " in s:
                parts = s.split(" to file ", 1)
                content_expr = parts[0][6:].strip()
                file_expr = parts[1].strip()
                content = str(eval_expr(content_expr, i+1))
                file_path = eval_expr(file_expr, i+1)
                try:
                    with open(file_path, 'w') as f:
                        f.write(content)
                except Exception as e:
                    raise EzScriptError(f"Cannot write to file '{file_path}': {e}", i+1)

            # APPEND FILE
            elif s.startswith("append ") and " to file " in s:
                parts = s.split(" to file ", 1)
                content_expr = parts[0][7:].strip()
                file_expr = parts[1].strip()
                content = str(eval_expr(content_expr, i+1))
                file_path = eval_expr(file_expr, i+1)
                try:
                    with open(file_path, 'a') as f:
                        f.write(content)
                except Exception as e:
                    raise EzScriptError(f"Cannot append to file '{file_path}': {e}", i+1)

            # IF / ELIF / ELSE
            elif (s.startswith("if ") and (s.endswith(" then") or s.endswith(":"))):
                if s.endswith(" then"):
                    condition = s[3:-5].strip()
                else:
                    condition = s[3:-1].strip()
                
                i += 1
                if_start = i
                
                # Find where if block ends
                if_end = i
                while if_end < len(lines):
                    l = lines[if_end]
                    if not l.strip() or is_comment(l):
                        if_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= current_indent:
                        break
                    if_end += 1
                
                # Execute if block if condition is true
                executed = False
                if eval_expr(condition, i):
                    run_block(lines, if_start, current_indent + 4, loop_context)
                    executed = True
                
                # Handle elif and else
                i = if_end
                while i < len(lines):
                    next_line = lines[i].strip()
                    next_indent = len(lines[i]) - len(lines[i].lstrip())
                    
                    if next_indent != current_indent:
                        break
                        
                    if next_line.startswith("elif ") and (next_line.endswith(" then") or next_line.endswith(":")) and not executed:
                        if next_line.endswith(" then"):
                            condition = next_line[5:-5].strip()
                        else:
                            condition = next_line[5:-1].strip()
                        
                        i += 1
                        block_start = i
                        
                        block_end = i
                        while block_end < len(lines):
                            l = lines[block_end]
                            if not l.strip() or is_comment(l):
                                block_end += 1
                                continue
                            l_indent = len(l) - len(l.lstrip())
                            if l_indent <= current_indent:
                                break
                            block_end += 1
                        
                        if eval_expr(condition, i):
                            run_block(lines, block_start, current_indent + 4, loop_context)
                            executed = True
                        
                        i = block_end
                    
                    elif (next_line == "else" or next_line == "else:"):
                        i += 1
                        block_start = i
                        
                        block_end = i
                        while block_end < len(lines):
                            l = lines[block_end]
                            if not l.strip() or is_comment(l):
                                block_end += 1
                                continue
                            l_indent = len(l) - len(l.lstrip())
                            if l_indent <= current_indent:
                                break
                            block_end += 1
                        
                        if not executed:
                            run_block(lines, block_start, current_indent + 4, loop_context)
                        
                        i = block_end
                        break
                    else:
                        break
                
                continue

            # LOOP (repeat N times)
            elif s.startswith("loop ") and s.endswith(" times:"):
                count_expr = s[5:-7].strip()
                count = int(eval_expr(count_expr, i+1))
                i += 1
                body_start = i
                
                body_end = i
                while body_end < len(lines):
                    l = lines[body_end]
                    if not l.strip() or is_comment(l):
                        body_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= current_indent:
                        break
                    body_end += 1

                for loop_idx in range(count):
                    variables['loop_index'] = loop_idx
                    try:
                        run_block(lines, body_start, current_indent + 4, loop_context=True)
                    except Break:
                        break
                    except Continue:
                        continue

                i = body_end
                continue

            # WHILE loop
            elif s.startswith("while ") and (s.endswith(":") or s.endswith(" then")):
                if s.endswith(" then"):
                    condition = s[6:-5].strip()
                else:
                    condition = s[6:-1].strip()
                
                i += 1
                body_start = i
                
                body_end = i
                while body_end < len(lines):
                    l = lines[body_end]
                    if not l.strip() or is_comment(l):
                        body_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= current_indent:
                        break
                    body_end += 1

                while eval_expr(condition, i):
                    try:
                        run_block(lines, body_start, current_indent + 4, loop_context=True)
                    except Break:
                        break
                    except Continue:
                        continue

                i = body_end
                continue

            # FOR EACH loop
            elif s.startswith("for each ") and " in " in s and (s.endswith(":") or s.endswith(" then")):
                if s.endswith(" then"):
                    parts = s[9:-5].split(" in ", 1)
                else:
                    parts = s[9:-1].split(" in ", 1)
                
                var_name = parts[0].strip()
                iterable_expr = parts[1].strip()
                iterable = eval_expr(iterable_expr, i+1)
                
                i += 1
                body_start = i
                
                body_end = i
                while body_end < len(lines):
                    l = lines[body_end]
                    if not l.strip() or is_comment(l):
                        body_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= current_indent:
                        break
                    body_end += 1

                for item in iterable:
                    variables[var_name] = item
                    try:
                        run_block(lines, body_start, current_indent + 4, loop_context=True)
                    except Break:
                        break
                    except Continue:
                        continue

                i = body_end
                continue

            # TRY-CATCH error handling
            elif s == "try:":
                i += 1
                try_start = i
                
                try_end = i
                while try_end < len(lines):
                    l = lines[try_end]
                    if not l.strip() or is_comment(l):
                        try_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= current_indent:
                        break
                    try_end += 1
                
                has_catch = try_end < len(lines) and lines[try_end].strip().startswith("catch")
                
                if not has_catch:
                    raise EzScriptError("try block must have a catch block", i)
                
                catch_line = lines[try_end].strip()
                error_var = None
                if catch_line == "catch:":
                    error_var = None
                elif catch_line.startswith("catch ") and catch_line.endswith(":"):
                    error_var = catch_line[6:-1].strip()
                else:
                    raise EzScriptError("Invalid catch syntax", try_end+1)
                
                catch_start = try_end + 1
                catch_end = catch_start
                while catch_end < len(lines):
                    l = lines[catch_end]
                    if not l.strip() or is_comment(l):
                        catch_end += 1
                        continue
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent <= current_indent:
                        break
                    catch_end += 1
                
                try:
                    run_block(lines, try_start, current_indent + 4, loop_context)
                except (Exception, EzScriptError) as e:
                    if isinstance(e, (Return, Break, Continue)):
                        raise
                    if error_var:
                        variables[error_var] = str(e)
                    run_block(lines, catch_start, current_indent + 4, loop_context)
                
                i = catch_end
                continue

            # LIST/STRING METHODS
            elif "." in s and "(" in s and ")" in s:
                # Check if it's a method call on a variable
                if s.startswith("let ") and " be " in s:
                    # Assignment from method call
                    parts = s.split(" be ", 1)
                    var = parts[0][4:].strip()
                    call_expr = parts[1]
                    result = eval_expr(call_expr, i+1)
                    variables[var] = result
                else:
                    # Just execute the method
                    eval_expr(s, i+1)

            # Function call (with or without assignment)
            elif "(" in s and ")" in s:
                if " be " in s and s.startswith("let "):
                    parts = s.split(" be ", 1)
                    var = parts[0][4:].strip()
                    call_expr = parts[1]
                    result = eval_expr(call_expr, i+1)
                    variables[var] = result
                else:
                    eval_expr(s, i+1)

        except EzScriptError as e:
            if e.line_number is None:
                e.line_number = i + 1
            raise
        except Exception as e:
            raise EzScriptError(str(e), i+1)

        i += 1

    return i

def run_file(file):
    """Run an EzScript file."""
    if not file.endswith(".ez"):
        raise Exception("EzScript files must end with .ez")

    variables.clear()
    functions.clear()

    try:
        with open(file) as f:
            content = f.read()
            lines = content.split("\n")
    except FileNotFoundError:
        print(f"Error: File '{file}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        run_block(lines, 0, 0)
    except Return:
        pass
    except EzScriptError as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"EzScript Error on line {e.line_number}:", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        if e.line_number and 0 < e.line_number <= len(lines):
            print(f"  {lines[e.line_number-1].strip()}", file=sys.stderr)
            print(f"  {'~' * len(lines[e.line_number-1].strip())}", file=sys.stderr)
        print(f"\n{e.message}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)
    run_file(sys.argv[1])