# EzScript Language Support for Visual Studio Code

This extension provides comprehensive language support for **EzScript** within Visual Studio Code.

## Features

- Syntax highlighting
- Code snippets
- Press F5 to run your `.ez` file
- More features coming soon

## Installation

1. Open the Extensions view in Visual Studio Code.
2. Search for **EzScript**.
3. Install the extension.

## Usage

Open any `.ez` file to activate EzScript language features.

When the extension activates it will attempt to download the interpreter into the extension's global storage folder and use it from there. This keeps the VSIX small and avoids the "file is large" publishing error.

## About EzScript

EzScript is a beginner-friendly, English-like programming language designed to be simple, readable, and powerful.

Example:

```
function factorial(n):
    if n is equal to 0 then
        return 1
    else:
        return n * factorial(n - 1)

let x be input("Enter a number: ")
let result be factorial(int(x))
print "Factorial of {x} is {result}"
