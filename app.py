from flask import Flask, render_template, request, url_for
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

OUTPUT_FOLDER = "static/outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CANVAS_SIZE = (1080, 1080)


def create_post(bg_path, logo_path, icons, headline, username, highlight_words, output_path):

    # Load Background
    bg = Image.open(bg_path).convert("RGBA")
    bg = bg.resize(CANVAS_SIZE)

    width, height = bg.size

    # -------- Professional News Black Overlay --------
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    fade_start = int(height * 0.05)
    mid_point = int(height * 0.55)

    for y in range(height):

        if y < fade_start:
            alpha = 0

        elif y < mid_point:
            progress = (y - fade_start) / (mid_point - fade_start)
            alpha = int(160 * (progress ** 1.3))

        else:
            progress = (y - mid_point) / (height - mid_point)
            alpha = 160 + int(95 * (progress ** 1.8))

        for x in range(width):
            gradient.putpixel((x, y), (0, 0, 0, alpha))

    bg = Image.alpha_composite(bg, gradient)
    draw = ImageDraw.Draw(bg)

    # Fonts
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "Nunito-SemiBold.ttf")

    headline_font = ImageFont.truetype(font_path, 72)
    small_font = ImageFont.truetype(font_path, 26)

    margin = 140
    max_width = width - margin * 2

    # Text wrapping
    words = headline.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        bbox = draw.textbbox((0, 0), test_line, font=headline_font)
        line_width = bbox[2]

        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "

    lines.append(current_line.strip())

    line_height = 95
    total_height = len(lines) * line_height

    y_text = height - total_height - 100

    highlight_set = set(w.strip().lower() for w in highlight_words.split(","))

    # Draw Headline
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_width = bbox[2]
        x = (width - line_width) // 2

        current_x = x

        for word in line.split():
            word_space = word + " "
            bbox = draw.textbbox((0, 0), word_space, font=headline_font)
            word_width = bbox[2]

            clean_word = word.strip(",.!?").lower()

            if clean_word in highlight_set:
                color = (255, 215, 0)
            else:
                color = (255, 255, 255)

            draw.text((current_x+2, y_text+2), word_space,
                      font=headline_font, fill=(0, 0, 0))
            draw.text((current_x, y_text), word_space,
                      font=headline_font, fill=color)

            current_x += word_width

        y_text += line_height

    # Username + Icons
    username_y = height - 80

    bbox = draw.textbbox((0, 0), username, font=small_font)
    username_width = bbox[2]

    total_icons_width = len(icons) * 40 + (len(icons) - 1) * 15 if icons else 0
    total_width = username_width + 20 + total_icons_width

    start_x = (width - total_width) // 2

    draw.text((start_x, username_y),
              username, font=small_font, fill="white")

    icon_x = start_x + username_width + 20

    for icon_path in icons:
        icon = Image.open(icon_path).convert("RGBA")
        icon.thumbnail((35, 35))
        bg.paste(icon, (icon_x, username_y - 5), icon)
        icon_x += 50

    # Logo Top Right
    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((160, 160))
    bg.paste(logo, (width - logo.width - 40, 40), logo)

    bg.convert("RGB").save(output_path)


@app.route("/", methods=["GET", "POST"])
def index():

    image_url = None

    if request.method == "POST":

        bg = request.files["background"]
        logo = request.files["logo"]
        icons = request.files.getlist("icons")

        headline = request.form["headline"]
        username = request.form["username"]
        highlight_words = request.form["highlight"]

        bg_path = os.path.join(OUTPUT_FOLDER, "bg.png")
        logo_path = os.path.join(OUTPUT_FOLDER, "logo.png")

        bg.save(bg_path)
        logo.save(logo_path)

        icon_paths = []
        for i, icon in enumerate(icons):
            path = os.path.join(OUTPUT_FOLDER, f"icon{i}.png")
            icon.save(path)
            icon_paths.append(path)

        output_path = os.path.join(OUTPUT_FOLDER, "final_output.png")

        create_post(
            bg_path,
            logo_path,
            icon_paths,
            headline,
            username,
            highlight_words,
            output_path
        )

        image_url = url_for('static',
                            filename='outputs/final_output.png')

    return render_template("index.html", image_url=image_url)


# 🔥 Production Ready Run (Render Compatible)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)