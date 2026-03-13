# Language D

Language D is a custom language prototype with:

- Python-like readable syntax
- C++ backend generation
- static type checking
- safer pointer handling
- built-in data structures and algorithms

Source files use the `.d` extension.

## Project Layout

- `langd.py`: compiler toolchain CLI
- `examples/demo.d`: sample Language D program
- `d_runtime/`: runtime for Python execution mode
- `ide/atom-language-d/`: Atom or Pulsar editor package
- `build/`: generated C++ and binaries

## Language Basics

Language D is indentation-based. Blocks end with `:`.

Keywords:

- `use`
- `fn`
- `let`
- `class`
- `struct`
- `ptr`
- `setptr`
- `if`, `elif`, `else`, `for`, `while`, `return`

Types currently supported:

- `Int`
- `Float`
- `Bool`
- `String`
- `Void`
- `Vector[T]` (example: `Vector[Int]`)

## Example

```d
use std

struct Point:
    let x: Int
    let y: Int

class Counter:
    let value: Int = 0

    fn inc(self, delta: Int) -> Void:
        self.value = self.value + delta

fn main() -> Int:
    let nums: Vector[Int] = [9, 3, 7, 1, 5]
    let sorted_nums: Vector[Int] = quick_sort(nums)

    ptr score: Int = 10
    print("pointer value:", val(score))
    setptr score = 42
    print("updated pointer value:", val(score))

    let c: Counter = Counter()
    c.inc(8)
    print("counter:", c.value)

    print("index of 7:", binary_search(sorted_nums, 7))
    return 0

main()
```

## Compiler Commands

From this folder:

```powershell
cd "c:\Users\Ashish\Desktop\Language prop\langugae D"
```

Type check:

```powershell
python langd.py check examples/demo.d
```

Run with Python backend:

```powershell
python langd.py run examples/demo.d
```

Show transpiled Python:

```powershell
python langd.py transpile examples/demo.d
```

Generate C++:

```powershell
python langd.py compile-cpp examples/demo.d -o build/demo.cpp
```

Compile generated C++ to native executable:

```powershell
g++ -std=c++20 build/demo.cpp -o build/demo.exe
```

Run native executable:

```powershell
.\build\demo.exe
```

## Full Flow

```powershell
python langd.py check examples/demo.d
python langd.py run examples/demo.d
python langd.py compile-cpp examples/demo.d -o build/demo.cpp
g++ -std=c++20 build/demo.cpp -o build/demo.exe
.\build\demo.exe
```

## Pointer Model

Language D pointer syntax maps to a safer runtime pointer wrapper.

```d
ptr score: Int = 10
print(val(score))
setptr score = 99
```

## Data Structures and Algorithms

With `use std`, available built-ins include:

- `Vector`
- `Stack`
- `Queue`
- `LinkedList`
- `HashMap`
- `quick_sort`
- `binary_search`
- `bfs`
- `dijkstra`

## IDE Support (Atom or Pulsar)

Package path:

- `ide/atom-language-d`

Provided features:

- `.d` syntax highlighting
- run/check/compile/build commands
- menu entries
- keybindings

Commands exposed by the package:

- `language-d:check`
- `language-d:run`
- `language-d:compile-cpp`
- `language-d:build-native`

Default keybindings:

- `F5`: run current `.d` file
- `Ctrl+Alt+C`: type check current `.d` file
- `Ctrl+Alt+B`: build and run native executable

## Notes

- Only `.d` files are accepted by `langd.py`.
- `python` must be in PATH.
- `g++` must be in PATH for native compilation.
- `build/` is ignored by git.
