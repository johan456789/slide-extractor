# slide-extractor

A script that extracts slides from lecture video and converts them into a searchable OCRed PDF.

This script extracts different frames from lecture videos in current directory recursively (`imagehash`, `cv2`), combine frames into image-only PDFs (`img2pdf`), OCR the frames and output text-only PDFs (`tesserect`, `ghostscript`), and merge text-only and image-only PDFs into high quality searchable lecture slides.



## Usage:

Put `slide-extractor.py` in the video directory, run `python slide-extractor.py`. The output PDFs will be stored in the same (sub)directories as those videos.



## Dependencies

```bash
brew install tesseract ghostscript
```

```python
pip install tqdm pillow imagehash opencv-python PyPDF2 img2pdf
```

Tested environment: Python 3.7.2, macOS

Homebrew packages: [tesserect](https://github.com/tesseract-ocr/tesseract), [ghostscript](https://www.ghostscript.com)

Python packages: [tqdm](https://tqdm.github.io), [pillow](https://pillow.readthedocs.io/en/stable/), [imagehash](https://github.com/JohannesBuchner/imagehash), [opencv-python](https://github.com/skvark/opencv-python), [PyPDF2](https://pythonhosted.org/PyPDF2/), [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf)

- Other possible candidate libraries for this tiny project and why they are not used:

  - [imagemagick](https://www.imagemagick.org): `convert *.png out.pdf`
    it re-encodes the image. With zip compression (-compress Zip) you can get lossless output, but the file will be larger. `img2pdf` does not re-encode by default, runs faster, and uses less memory, so `img2pdf` is used.

  - [OCRmyPDF](https://github.com/jbarlow83/OCRmyPDF): `ocrmypdf in.pdf out-ocr.pdf`
    Tesseract & ghostscript pipeline is actually faster and has better image quality, as it uses the original images in OCRed PDFs (downsides: high I/O, larger output files), so `ocrmypdf` is not used. If smaller PDF is desired, just do further compression using other software.

    ```bash
    $ time (for i in frame*.png; do tesseract -c textonly_pdf=1 $i $i pdf; done; gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=combine-text.pdf -dBATCH frame*.pdf; python merge.py;)
    
    real	0m35.962s
    user	0m28.935s
    sys	0m1.890s
    
    $ time ocrmypdf in.pdf out-ocr.pdf
    
    real	0m39.866s
    user	1m11.777s
    sys	0m7.876s
    ```



## Sidenote

This program is intended for use on MOOC videos. For Cousera and edX, you can check out [coursera-dl](https://github.com/coursera-dl/coursera-dl) and [edx-dl](https://github.com/coursera-dl/edx-dl) to download videos in batch.
