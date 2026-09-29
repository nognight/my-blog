---
title: 'Rust for Beginners: Build Your First Command-Line Program'
pubDate: '2026-09-29'
description: 'Learn Rust step by step: set up Cargo, explore variables and functions, understand ownership, and build a command-line temperature converter.'
heroImage: '../../assets/blog-placeholder-4.jpg'
tags:
  - rust
  - beginners
  - programming
---

Rust is a compiled programming language used for command-line tools, web services, and systems software. Its compiler checks types and ownership rules before your program runs, helping catch mistakes early.

This lesson starts from an empty project and ends with a temperature converter. You only need a terminal and a text editor. Each Rust code block below is a complete program: replace `src/main.rs` with one example at a time, then run `cargo run`.

## 1. Install Rust and create a project

Follow the [official Rust installation instructions](https://rust-lang.org/tools/install/) for your operating system. The recommended rustup installer provides Rust and Cargo, its project and package manager. Windows setup may also require the Visual Studio C++ build tools described on that page.

Open a new terminal after installation and check:

```sh
rustc --version
cargo --version
```

Create your first project:

```sh
cargo new rust_starter
cd rust_starter
cargo run
```

You should see `Hello, world!` after Cargo's build messages. The important files are:

- `Cargo.toml`: your project's name, settings, and dependencies.
- `src/main.rs`: the starting point for this executable.
- `Cargo.lock`: the resolved dependency versions.

Cargo writes build output into `target/`. See the Rust Book's [Cargo introduction](https://doc.rust-lang.org/book/ch01-03-hello-cargo.html) for more details.

## 2. Read your first Rust program

Replace `src/main.rs` with:

```rust
fn main() {
    let name = "Rust beginner";
    println!("Hello, {name}!");
}
```

`fn` defines a function, and `main` is where execution begins. Braces surround its body. `let` creates a variable, and `println!` prints a line. The exclamation mark means it is a macro. `{name}` inserts the variable into the output.

## 3. Variables, types, and mutability

Variables are immutable by default. Add `mut` when a value needs to change:

```rust
fn main() {
    let language = "Rust";
    let mut lessons_completed: u32 = 0;
    lessons_completed += 1;

    let temperature: f64 = 21.5;
    let is_learning: bool = true;

    println!("Learning {language}: {lessons_completed} lesson completed");
    println!("Temperature: {temperature}, still learning: {is_learning}");
}
```

Rust can infer many types, but annotations make some choices explicit. Here, `u32` is an unsigned 32-bit integer, `f64` is a 64-bit floating-point number, and `bool` holds `true` or `false`.

If you remove `mut`, the assignment to `lessons_completed` fails to compile. Read the compiler's message: it identifies the variable and often suggests a fix.

## 4. Functions and control flow

Functions declare parameter types and use `->` for their return type:

```rust
fn celsius_to_fahrenheit(celsius: f64) -> f64 {
    celsius * 9.0 / 5.0 + 32.0
}

fn main() {
    for celsius in [0.0, 20.0, 100.0] {
        let fahrenheit = celsius_to_fahrenheit(celsius);
        let label = if celsius <= 0.0 { "freezing or below" } else { "above freezing" };
        println!("{celsius} C = {fahrenheit} F ({label})");
    }
}
```

The function returns its final expression without a semicolon. Adding a semicolon there discards that value, causing a type error because the function promises an `f64`.

The `for` loop visits each array element. An `if` expression can also produce a value, so both branches here return text for `label`.

## 5. Ownership and borrowing

A `String` owns its text. Assigning it to another variable moves ownership:

```rust
fn main() {
    let original = String::from("Hello, Rust");
    let moved = original;

    println!("{moved}");
    // println!("{original}"); // Uncomment to see a use-after-move error.
}
```

After the move, `original` is no longer usable. Simple types such as integers implement `Copy`, so assigning them copies their value instead.

When a function only needs to read text, borrow it:

```rust
fn greet(name: &str) {
    println!("Hello, {name}!");
}

fn main() {
    let mut name = String::from("Rust");
    greet(&name);
    name.push_str(" beginner");
    greet(&name);
}
```

`&name` borrows the value. The function accepts `&str`, a borrowed view of text, without taking ownership. Once that borrow is no longer used, we can change `name`.

Rust permits multiple shared references or one exclusive mutable reference to the same data at a time. References must also remain valid. These rules prevent conflicting access and dangling references in safe Rust. The Rust Book explains [references and borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html) with more examples.

## 6. Build a temperature converter

Now combine functions, variables, and control flow with terminal input. Replace `src/main.rs` with:

```rust
use std::io;

fn celsius_to_fahrenheit(celsius: f64) -> f64 {
    celsius * 9.0 / 5.0 + 32.0
}

fn main() {
    println!("Enter a temperature in Celsius:");

    let mut input = String::new();

    if let Err(error) = io::stdin().read_line(&mut input) {
        eprintln!("Could not read input: {error}");
        return;
    }

    let celsius: f64 = match input.trim().parse() {
        Ok(value) => value,
        Err(_) => {
            eprintln!("Please enter a number, such as 20 or -5.5.");
            return;
        }
    };

    if !celsius.is_finite() {
        eprintln!("Please enter a finite temperature.");
        return;
    }

    let fahrenheit = celsius_to_fahrenheit(celsius);
    if !fahrenheit.is_finite() {
        eprintln!("That temperature is too large to convert.");
        return;
    }

    println!("{celsius:.1} C = {fahrenheit:.1} F");
}
```

Run `cargo run`, enter `20`, and press Enter:

```text
Enter a temperature in Celsius:
20
20.0 C = 68.0 F
```

Here is how the new syntax works:

- `use std::io` brings the standard library's input/output module into scope.
- `&mut input` lets `read_line` borrow and modify the string.
- `trim()` removes surrounding whitespace, including the newline from Enter.
- `parse()` converts text to a number; the `f64` annotation tells Rust which type to parse.
- `Result` represents success with `Ok` or failure with `Err`. The `match` handles both possibilities; `if let Err(...)` handles only the failure case for reading input.
- `return` exits `main` early, and `eprintln!` writes an error message to standard error.
- `:.1` displays one digit after the decimal point.

Try `0`, `100`, `-40`, and `hello`. The first three should produce `32.0`, `212.0`, and `-40.0` Fahrenheit. The last should show the friendly error message.

## 7. Practice before moving on

Use these commands from the project directory:

```sh
cargo fmt
cargo check
cargo run
```

They format your code, check it for compilation errors, and run it. If `cargo fmt` is unavailable, install its component with `rustup component add rustfmt`.

For practice, add a Fahrenheit-to-Celsius function using `(fahrenheit - 32.0) * 5.0 / 9.0`. Then let the user choose which conversion to run. Finally, put the input steps inside a `loop` so the program can accept another temperature without restarting.

When a compiler error appears, fix the first reported problem and run `cargo check` again. Getting comfortable with that feedback is a useful part of learning Rust.
