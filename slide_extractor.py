import os, glob
import subprocess
import argparse
from tqdm import tqdm
from PIL import Image
import imagehash
import cv2
import PyPDF2


CHECK_PER_FRAMES = 30 # check per 30 frames (i.e. 1 frame per sec for 30 fps video)
DIFF_THRESHOLD = 3
FNULL = open(os.devnull, 'w')
INCLUDE_TEST = False

def subprocess_combine_image_pdf():
    # subprocess.call(['bash', '-c', 'convert frame*.png combine-img.pdf'], stdout=FNULL, stderr=subprocess.STDOUT) # imagicmagick
    subprocess.call(['bash', '-c', 'img2pdf frame*.png -o combine-img.pdf'], stdout=FNULL, stderr=subprocess.STDOUT)

def subprocess_ocr_images():
    directory = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(directory) if f.startswith('frame') and f.endswith('.png')]
    for f in files:
        comd = f'tesseract -c textonly_pdf=1 {f} {f.replace(".png","")} pdf'
        subprocess.call(['bash', '-c',comd])

def subprocess_text_only_pdf():
    subprocess.call(['bash', '-c', 'gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=combine-text.pdf -dBATCH frame*.pdf;'], stdout=FNULL, stderr=subprocess.STDOUT)

def subprocess_remove_temp_files():
    subprocess.call(['bash', '-c', 'rm -f frame*.png frame*.pdf combine-*.pdf'])


def generate_frames(filename):
        basename = os.path.basename(filename).replace('.mp4','')
        tqdm.write('Extracting key frames from ' + filename + ', may take a minute...')

        cap = cv2.VideoCapture(filename)
        success, cv2_im = cap.read()
        count = 0
        idx = 0
        im_hash = "0123456789abcdef" # just an arbitrary hash
        while success:
            for i in range(CHECK_PER_FRAMES): # skip frames
                success, cv2_im = cap.read()
            if not success:
                return basename, idx

            cv2_im = cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB)
            pil_im = Image.fromarray(cv2_im)

            # compare current frame to previous frame, save frame if sufficiently different
            prev_im_hash = im_hash
            im_hash = imagehash.phash(pil_im)
            # tqdm.write(str(count) + ' ' +  str(im_hash)) # print current frame & its image hash
            if idx == 0 or im_hash - prev_im_hash > DIFF_THRESHOLD:
                # tqdm.write('|------------|\n| save frame |\n|------------|')
                pil_im.save('frame{}.png'.format(str(idx).zfill(3)), dpi=(72, 72))
                idx += 1
            count += 1
        return basename, idx


def main():
    global INCLUDE_TEST
    search_pattern = ""
    parser = argparse.ArgumentParser(description="Process mp4 files.")
    parser.add_argument('--include-test', action='store_true', 
                        help='Include mp4 files in the test directory.')
    args = parser.parse_args()

    if args.include_test or INCLUDE_TEST:
        search_pattern = '**/*.mp4'
    else:
        # This excludes mp4 files in the 'test' directory specifically.
        search_pattern = '[!test]**/*.mp4'
    for filename in tqdm(sorted(glob.glob(search_pattern, recursive=True))):
        #Basename tracks the title
        #Frames are generated from the filename in format framei.png
        basename, count = generate_frames(filename)
        # bash script subproccess needs: img2pdf, tesseract, ghostscript
        tqdm.write(f'Generating image-only PDF with {count} frames...')
        #makes combine-img.pdf
        subprocess_combine_image_pdf()

        tqdm.write('Running OCR...')
        subprocess_ocr_images()
        #makes framei.png to framei.pdf
        #subprocess.call(['bash', '-c', 'for i in frame*.png; do tesseract -c textonly_pdf=1 $i ${i%.*} pdf; done;'], stdout=FNULL, stderr=subprocess.STDOUT)

        tqdm.write('Generating text-only PDF...')
        #makes combine-text.pdf
        subprocess_text_only_pdf()

        tqdm.write('Merging image-only & text-only PDF...')
        # merge combine-text.pdf and combine-img.pdf
        merge('combine-text.pdf', 'combine-img.pdf', basename + '.pdf') # save file where video file is

        tqdm.write('Temporary files removed\n')
        #removes temp files
        subprocess_remove_temp_files()

def distance(s1, s2):
    # return distance of two hashes
    if len(s1) != len(s2):
        raise ValueError("Undefined for sequences of unequal length")
    return sum(abs(int(ch1, 16)-int(ch2, 16)) for ch1, ch2 in zip(s1, s2))

# Function Author: https://github.com/gsauthof
# copied from pdfmerge.py (https://github.com/gsauthof/utility/blob/master/pdfmerge.py)
def merge(textonlyPDF, imageonlyPDF, ofilename):
    '''
    Merge text-only and image-only PDFs into one
    e.g. text, images, merged
    cf. https://github.com/tesseract-ocr/tesseract/issues/660#issuecomment-273629726
    '''
    with open(textonlyPDF, 'rb') as f1, open(imageonlyPDF, 'rb') as f2:
        # PdfReader isn't usable as context-manager
        pdf1, pdf2 = (PyPDF2.PdfReader(x) for x in (f1, f2))
        opdf = PyPDF2.PdfWriter()
        for page1, page2 in zip(pdf1.pages, pdf2.pages):
            page1.merge_page(page2)
            opdf.add_page(page1)
        n1, n2 = len(pdf1.pages), len(pdf2.pages)
        if n1 != n2:
            for page in (pdf2.pages[n1:] if n1 < n2 else pdf1.pages[n2:]):
                opdf.add_page(page)
        with open(ofilename, 'wb') as g:
            opdf.write(g)


if __name__ == '__main__':
    main()
