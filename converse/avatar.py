import sys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from random import random
import os.path
import re

class AvatarFactory:
    def __init__(self, square_size=200):
        self.square_size = square_size

    def generate(self, name, output_stream):
        bg = self.background_color()
        fg = (255, 255, 255)
        fg = tuple(int(255 - (i/8)) for i in bg)
        image = Image.new('RGBA', (self.square_size, self.square_size),
                          bg)
        draw = ImageDraw.Draw(image)
        text = self.text(name)
        font = self.font()
        textwidth, textheight = font.getsize(text)
        left = ((self.square_size - textwidth) / 2.0)
        top = (self.square_size - textheight) / (2 * 1.2)

        draw.text((left, top), text, fill=fg, font=font)
        image.save(output_stream, 'PNG')
        return True

    def text(self, name):
        """
            Some improvements:
            - remove uninteresting symbols. E.g. (wrong) i_v_o -> i_
            - Look at caps: VladDrac -> VD

        """

        words = re.split("[\s_-]", name.strip("-_ "))
        if len(words) == 1:
            return words[0][:2].upper()
        else:
            return (words[0][0] + words[-1][0]).upper()

    def background_color(self):
        """Pick a random color background color.
        The background color should not be too bright, since the foreground
        font color defaults to white.
        """
        while True:
            red = int(random() * 256)
            green = int(random() * 256)
            blue = int(random() * 256)
            color = red, green, blue

            if sum(color) < 400 and max(color) - min(color) > 30:
                return color

    def font(self):
        """Return a PIL ImageFont instance.
        """
        path = os.path.join(os.path.dirname(__file__), 'font',
                            'FantasqueSansMono-BoldItalic.ttf')
        size = int(self.square_size * 0.8)
        return ImageFont.truetype(path, size=size)


if __name__ == '__main__':
    f = AvatarFactory()
    with open(sys.argv[2], "wb") as o:
        f.generate(sys.argv[1], o)
    print("Written avatar for {0} to {1}".format(sys.argv[1], sys.argv[2]))
