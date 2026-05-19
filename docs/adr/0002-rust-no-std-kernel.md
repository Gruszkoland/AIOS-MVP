# ADR-0002: Rust no_std jako język kernela

## Status
Accepted

## Decyzja
Kernel AIOS pisany w Rust z `#![no_std]`.

## Uzasadnienie
- memory safety bez GC
- brak undefined behavior z domyślnego modelu Rusta
- bogate wsparcie dla bare-metal (`x86_64-unknown-none`, `aarch64-unknown-none`)
- llvm jako backend

## Ograniczenia
- brak `std` — własna implementacja alokatorów
- nightly toolchain dla niektórych feature (inline assembly, custom allocators)
- potrzebny Miri do weryfikacji unsafe

## Alternatywy odrzucone
- C: brak memory safety
- Zig: mniejszy ekosystem
- Go: GC nieakceptowalny w kernelu
