import os
from pathlib import Path

import lhafile


def get_content_from_compressed_file(compress_file_path: Path):
    f = lhafile.Lhafile(str(compress_file_path))
    for info in f.infolist():

        with open(compress_file_path.parent / info.filename, "wb") as tf:
            content = f.read(info.filename)
        return content

def batch_uncompress_file(directory):
    dir = Path(directory)
    all_compressed_file_list = list(dir.rglob("*.lzh"))
    for compressed_file in all_compressed_file_list:
        save_dir = Path("uncompressed_data") / compressed_file.parent.parts[-1]
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)
        content = get_content_from_compressed_file(compressed_file)
        file_name = compressed_file.name
        text = str(content.decode("ansi")).rsplit("\n")
        with open((save_dir / file_name).with_suffix(".txt"), "w", encoding="utf-8") as f:
            f.writelines(text)
        
if __name__=='__main__':
    batch_uncompress_file("compressed_data")
