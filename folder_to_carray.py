#!/usr/bin/env python3
"""
folder_to_carrays.py

Recursively converts all files in a folder into C-style byte arrays.
Generates:
  - embedded_build.c → contains the arrays and file map
  - embedded_build.h → contains externs + struct definition

Build by: Cao Khai Minh
Update Date: 19/09/2025

Usage:
    python3 folder_to_carrays.py <input_folder> <output_base>
Example:
    python3 folder_to_carrays.py build embedded_build
This produces embedded_build.c and embedded_build.h
"""

import sys
import os
import mimetypes

# -----------------------------
# Args
# -----------------------------
if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <input_folder> <output_base>")
    sys.exit(1)

input_folder = sys.argv[1]
output_base = sys.argv[2]
c_file = output_base + ".c"
h_file = output_base + ".h"

if not os.path.isdir(input_folder):
    print(f"Error: Folder '{input_folder}' not found")
    sys.exit(1)

# -----------------------------
# Helpers
# -----------------------------
def to_c_identifier(path: str) -> str:
    """Sanitize file path into valid C identifier"""
    return (
        path.replace("/", "_")
            .replace("\\", "_")
            .replace("-", "_")
            .replace(".", "_")
    )

def guess_mime_type(file_path: str) -> str:
    mime, _ = mimetypes.guess_type(file_path)
    return mime if mime else "application/octet-stream"

def file_to_c_array(file_path, array_name, f_c):
    """Write one file as a C string literal with hex escapes"""
    with open(file_path, "rb") as f_in:
        data = f_in.read()

    f_c.write(f"// File: {file_path}\n")
    f_c.write(f"const unsigned char {array_name}[] = \n")

    # Write as string literal with hex escapes, wrap lines for readability
    line = '"'
    for i, b in enumerate(data):
        line += f"\\x{b:02x}"
        if (i + 1) % 16 == 0:  # wrap every 16 bytes
            f_c.write(line + '"\n')
            line = '"'
    if line != '"':  # flush remainder
        f_c.write(line + '"\n')

    f_c.write(";\n")
    f_c.write(f"const unsigned int {array_name}_len = {len(data)};\n\n")

# -----------------------------
# Generate files
# -----------------------------
file_entries = []

with open(c_file, "w") as f_c, open(h_file, "w") as f_h:
    # --- Header file ---
    f_h.write("// Auto-generated header for embedded files\n\n")
    f_h.write("typedef struct {\n")
    f_h.write("    const char *uri;\n")
    f_h.write("    const unsigned char *data;\n")
    f_h.write("    unsigned int length;\n")
    f_h.write("    const char *content_type;\n")
    f_h.write("} embedded_file_t;\n\n")

    # --- C file ---
    f_c.write("// Auto-generated embedded files\n\n")
    f_c.write('#include "embedded_build.h"\n\n')

    # Convert all files
    for root, _, files in os.walk(input_folder):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(full_path, input_folder).replace("\\", "/")
            array_name = to_c_identifier(rel_path)
            mime_type = guess_mime_type(full_path)

            file_to_c_array(full_path, array_name, f_c)

            f_h.write(f"extern const unsigned char {array_name}[];\n")
            f_h.write(f"extern const unsigned int {array_name}_len;\n")

            file_entries.append((rel_path, array_name, mime_type))

    # File map in C file
    f_c.write("embedded_file_t embedded_files[] = {\n")
    for rel_path, array_name, mime_type in file_entries:
        f_c.write(
            f'    {{"/{rel_path}", {array_name}, {array_name}_len, "{mime_type}"}},\n'
        )
        if rel_path == "index.html":
            f_c.write(
                f'    {{"/", {array_name}, {array_name}_len, "{mime_type}"}},\n'
            )
    f_c.write("};\n\n")
    f_c.write("int embedded_files_count = sizeof(embedded_files) / sizeof(embedded_files[0]);\n")

    # Externs for map
    f_h.write("\nextern embedded_file_t embedded_files[];\n")
    f_h.write("extern int embedded_files_count;\n")

print(f"✅ Generated {c_file} and {h_file}")

