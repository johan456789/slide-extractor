# -*- coding: utf-8 -*-
# @Author: johan
# @Date:   2019-02-15 01:47:00
# @Last Modified by:   johan
# @Last Modified time: 2019-02-16 19:54:57

import os, glob
import subprocess

from tqdm import tqdm
from PIL import Image
import imagehash
import cv2
import PyPDF2


CHECK_PER_FRAMES = 30 # check per 30 frames (i.e. 1 frame per sec for 30 fps video)
DIFF_THRESHOLD = 3

def main():
	for filename in tqdm(sorted(glob.glob('**/*.mp4', recursive=True))):
		basename = os.path.basename(filename)
		purename = os.path.splitext(basename)[0]
		tqdm.write('Extracting key frames from ' + basename + ', may take a minute...')

		cap = cv2.VideoCapture(filename)
		success, cv2_im = cap.read()
		count = 0
		idx = 0
		im_hash = "0123456789abcdef" # just an arbitrary hash
		while success:
			for i in range(CHECK_PER_FRAMES): # skip frames
				success, cv2_im = cap.read()
			if not success:
				break

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

		# bash script: img2pdf, tesseract, ghostscript
		FNULL = open(os.devnull, 'w')
		tqdm.write('Generating image-only PDF...')
		# subprocess.call(['bash', '-c', 'convert frame*.png combine-img.pdf'], stdout=FNULL, stderr=subprocess.STDOUT) # imagicmagick
		subprocess.call(['bash', '-c', 'img2pdf frame*.png -o combine-img.pdf'], stdout=FNULL, stderr=subprocess.STDOUT)
		tqdm.write('Running OCR...')
		subprocess.call(['bash', '-c', 'for i in frame*.png; do tesseract -c textonly_pdf=1 $i $i pdf; done;'], stdout=FNULL, stderr=subprocess.STDOUT)
		tqdm.write('Generating text-only PDF...')
		subprocess.call(['bash', '-c', 'gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=combine-text.pdf -dBATCH frame*.pdf;'], stdout=FNULL, stderr=subprocess.STDOUT)

		# merge pdf
		tqdm.write('Merging image-only & text-only PDF...')
		merge('combine-text.pdf', 'combine-img.pdf', filename + '.pdf') # save file where video file is
		tqdm.write('Temporary files removed\n')
		subprocess.call(['bash', '-c', 'rm frame*.png frame*.pdf combine-*.pdf'])

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
		# PdfFileReader isn't usable as context-manager
		pdf1, pdf2 = (PyPDF2.PdfFileReader(x) for x in (f1, f2))
		opdf = PyPDF2.PdfFileWriter()
		for page1, page2 in zip(pdf1.pages, pdf2.pages):
			page1.mergePage(page2)
			opdf.addPage(page1)
		n1, n2 = len(pdf1.pages), len(pdf2.pages)
		if n1 != n2:
			for page in (pdf2.pages[n1:] if n1 < n2 else pdf1.pages[n2:]):
				opdf.addPage(page)
		with open(ofilename, 'wb') as g:
			opdf.write(g)


if __name__ == '__main__':
	main()