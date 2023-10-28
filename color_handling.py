def hex_to_rgb(hex_color):
    # Convert hexadecimal to RGB
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    # Convert RGB to hexadecimal
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def blend_hex_colors(color1, color2):
    # Convert hex colors to RGB
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    # Calculate the average of each RGB component
    avg_rgb = tuple((a + b) // 2 for a, b in zip(rgb1, rgb2))

    # Convert the average RGB back to a hexadecimal color
    blended_color = rgb_to_hex(avg_rgb)

    return blended_color

if __name__ == "__main__":
    # Two hex colors to blend
    hex_color1 = "#FF5733"
    hex_color2 = "#33FF77"

    # Get the average color
    average_color = blend_hex_colors(hex_color1, hex_color2)
    print("Average color:", average_color)