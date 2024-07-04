import os
import argparse
from PIL import Image
from colorama import init


init(autoreset=True)
parser: argparse.ArgumentParser = argparse.ArgumentParser()


def cls() -> None:
    os.system("cls" if os.name == "nt" else "clear")


ASCII_CHARS: list[str] = [".", ",", ":", ";", "+", "*", "?", "%", "S", "#", "@"]


def resize_image(image: Image.Image, a: float, new_width: int) -> Image.Image:
    aspect_ratio: float = image.height / float(image.width)
    new_height = int(aspect_ratio * new_width * a)

    return image.resize((new_width, new_height))


def map_pixels_to_ascii(image: Image.Image, ascii_chars: list[str]) -> str:
    pixels: list[list[int]] = image.getdata()
    ascii_str = ""
    for pixel in pixels:
        ascii_str += ascii_chars[pixel // 25]
    return ascii_str


def rgb_to_ansi_colour_code(r: int, g: int, b: int, is_background: bool) -> str:
    """Converts 0-255 RGB values to ANSI 256 colour code and returns the corresponding ANSI escape code."""
    r = r // 51
    g = g // 51
    b = b // 51

    colour_code: int = 16 + 36 * r + 6 * g + b
    prefix: str = "48" if is_background else "38"

    return f"\033[{prefix};5;{colour_code}m"


def rgb_to_ansi_24bit(
    pixel_index: int,
    pixel_values: list[list[int]],
    img_width: int,
    img_height: int,
    add_background: bool,
) -> str:
    """Converts 0-255 RGB values to ANSI 24bit colour"""
    relative_indices: list[int] = [
        -img_width - 1,
        -img_width,
        -img_width + 1,
        -1,
        1,
        img_width - 1,
        img_width,
        img_width + 1,
    ]

    neighbors: list[int] = []
    for idx in relative_indices:
        neighbor_row: int = (pixel_index + idx) // img_width
        neighbor_col: int = (pixel_index + idx) % img_width

        if 0 <= neighbor_row < img_height and 0 <= neighbor_col < img_width:
            neighbors.append(pixel_values[pixel_index + idx])

    r, g, b = pixel_values[pixel_index][:3]

    if add_background:
        rs: int = [pixel[0] for pixel in neighbors]
        gs: int = [pixel[1] for pixel in neighbors]
        bs: int = [pixel[2] for pixel in neighbors]

        # simple box blur idk
        ar: int = sum(rs) // len(rs) if rs else 0
        ag: int = sum(gs) // len(gs) if gs else 0
        ab: int = sum(bs) // len(bs) if bs else 0

        return f"\033[38;2;{r};{g};{b};48;2;{ar};{ag};{ab}m"

    return f"\033[38;2;{r};{g};{b}m"


def image_to_coloured_ascii(
    image_path: str, width: int, aspect_ratio: float, is_256: bool, add_bg: bool
) -> str | None:
    try:
        image: Image.Image = Image.open(image_path)
    except Exception as e:
        print(e)
        return

    image: Image.Image = resize_image(image, aspect_ratio, width)

    grayscale_image: Image.Image = image.convert("L")
    ascii_str: str = map_pixels_to_ascii(grayscale_image, ASCII_CHARS)

    coloured_ascii_list: list[str] = [""]
    pixels: list[list[int]] = image.getdata()

    if is_256:
        for pixel in pixels:
            r, g, b = pixel[:3]
            colour: str = rgb_to_ansi_colour_code(r, g, b, add_bg)

    for i in range(len(pixels)):
        colour: str = rgb_to_ansi_24bit(i, pixels, width, image.height, add_bg)
        coloured_ascii_list.append(f"{colour}{ascii_str[i]}")

    ascii_img = ""

    for i in range(0, len(coloured_ascii_list), width):
        ascii_img += "".join(coloured_ascii_list[i : i + width]) + "\033[39;49m" + "\n"

    return ascii_img


if __name__ == "__main__":
    parser.add_argument("path", help="Path to the input image file")
    
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=100,
        help="Set the character width for the ASCII converted image. [Default: 100]",
    )
    parser.add_argument(
        "-a",
        "--aspect_ratio",
        type=float,
        default=0.55,
        help="Adjust the aspect ratio to account for the height of your font, since characters are not square. [Default: 0.55]",
    )
    parser.add_argument(
        "-s",
        "--clearScreen",
        action="store_true",
        help="Clear the terminal screen before printing the ASCII image",
    )
    parser.add_argument(
        "-c",
        "--colour256",
        action="store_true",
        help="Use 256-colour ANSI mode (less vibrant). If not set, use 24-bit colour mode (more vibrant)",
    )
    parser.add_argument(
        "-b",
        "--background",
        action="store_true",
        help="Add background colours to the pixels, which can sometimes produce unexpected results",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Generate a .txt file with all the ANSI codes included. Note: The output file can be very large and unoptimized for filesize",
    )

    args: argparse.Namespace = parser.parse_args()

    image_path: str = args.path
    image_width: int = args.width | 100
    aspect_ratio: float = args.aspect_ratio | 0.55

    clear: bool = args.clearScreen | False
    colour_mode: bool = args.colour256 | False
    add_bg: bool = args.background | False
    make_output: bool = args.output | False

    ascii_img: str | None = image_to_coloured_ascii(
        image_path, image_width, aspect_ratio, colour_mode, add_bg
    )

    if clear:
        cls()

    print(ascii_img)

    if make_output:
        with open("ansi_image.txt", "w") as f:
            for line in ascii_img.splitlines():
                plain_line: str = "".join(line)
                f.write(plain_line)
