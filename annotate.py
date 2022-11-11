'''Annotate images with text using a csv look-up table.'''
import argparse
from csv import DictReader
from datetime import datetime
import logging
import os
import toml
from PIL import (Image,
                 ImageDraw,
                 ImageFont, 
                 UnidentifiedImageError)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    prog='Annotate Sample Images',
    description='Draw useful annotations over images using sample code look-up.',
    epilog='Script by Robert Pazdzior (2022) <rpazdzior@protonmail.com>'
)

parser.add_argument('annotation_csv',
    # required=True,
    help='''Annotation look-up sheet.
    \nShould contain a 'sample' column with name that matches part of the
    image file name. All other named columns are used as annotations.''')
parser.add_argument('input_dir',
    # required=True,
    help='Directory containing images to be annotated.')
parser.add_argument('output_dir',
    # required=True,
    help='Destination folder for the annotated images.')
parser.add_argument('-v', '--verbose', action='store_true',
    # required=True,
    )


def import_annotation(annotations_csv=''):
    '''Import the sample annotation look-up table CSV.'''
    # Read in CSV to list of dicts
    with open(annotations_csv, encoding='utf8') as annot:
        reader = DictReader(annot)
        annot_list_dicts = [d for d in reader]

    # convert sample row to primary dict keys with annotation objects
    annot_sample_keyed = {}
    for row in annot_list_dicts:
        sample = row.pop('sample')
        if sample in annot_sample_keyed:
            raise ValueError(f"Duplicate sample name found in '{annotations_csv}' => {sample}")
        annot_sample_keyed[sample] = row
    return annot_sample_keyed

def annotate_img(img:Image.Image, annotation:dict, formatting:dict):
    '''Draw annotation `annotation` over `img`'''
    default_font_size = formatting['font_size']
    font = ImageFont.truetype(r"C:\Windows\Fonts\LTYPE.TTF", default_font_size)
    text = ''
    for sample,vals in annotation.items():
        text = text + sample
        for title,val in vals.items():
            text = text + f'\n{title}: {val}'
    draw = ImageDraw.Draw(img)
    draw.text(
        (formatting['position_x'], formatting['position_y']),
        text = text,
        font = font,
        fill = (255,255,255),       # white fill
        stroke_fill = (0, 0, 0),    # black outline/stroke
        stroke_width = formatting['stroke_width']
    )
    return img

def lookup_annotation(imgfilename:str, annots:dict):
    '''Fetch annotation from look-up table if possible.'''
    annotation = {}
    samples = list(annots.keys())
    for sample in samples:
        if sample in imgfilename:
            annotation[sample] = annots[sample]
    if not annotation:
        logger.warning('No samples found matching %s. Skipped.', imgfilename)
    else:
        logger.info('%s matched sample "%s"', imgfilename, list(annotation.keys())[0])
    return annotation

def import_images(source_dir):
    '''Return dict of valid images from source dir.'''
    imgs = {}
    for file in os.listdir(source_dir):
        try:
            img = Image.open(source_dir + file)
            imgs[file] = img
            logging.debug('%s succesfully imported.', file)
        except UnidentifiedImageError:
            logging.debug('%s is not a valid image. Skipping file.', file)

    return imgs

if __name__ == "__main__":
    args = parser.parse_args()
    if args.verbose:
        logger.level = logging.INFO
        # logging.getLogger('PIL').setLevel(logging.WARNING)

    with open('./config.toml', encoding='utf8') as cfg:
        config = toml.load(cfg)

    annotations = import_annotation(args.annotation_csv)
    images = import_images(args.input_dir)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    output_dir = args.output_dir + datetime.now().strftime("/%Y-%m-%d_%H-%M-%S/")
    os.makedirs(output_dir)

    for filename,image in images.items():
        ann_img = annotate_img(
            image,
            lookup_annotation(filename, annotations),
            config['formatting'])
        ann_img.save(output_dir + filename)
