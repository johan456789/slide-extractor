import os
import sys
import pytest
import PyPDF2
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from slide_extractor import generate_frames, subprocess_combine_image_pdf, subprocess_ocr_images, subprocess_text_only_pdf, subprocess_remove_temp_files, merge
basename = ""


@pytest.fixture(scope="session", autouse=True)
def setup_include_test():
    import slide_extractor
    slide_extractor.INCLUDE_TEST = True


# 1. Testing title extraction and frame generation
@pytest.mark.run(order=1)
def test_generate_frames():
    #for filename in tqdm(sorted(glob.glob('**/*.mp4', recursive=True))):
    global basename
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(os.getcwd(),"test", "Example","Presentation.mp4")
    #print(fname)
    basename, count = generate_frames(fname)
    assert os.path.exists(fname), f"File {fname} does not exist!"
    assert basename == "Presentation"
    assert count > 0


# 2. Testing bash script functionality
@pytest.mark.run(order=2)
def test_subprocess_combine_image_pdf():
    subprocess_combine_image_pdf()
    assert os.path.exists('combine-img.pdf')

@pytest.mark.run(order=3)
def test_subprocess_ocr_images():
    invisible_texts_found = 0
    subprocess_ocr_images()
    # Assuming you know the frame count
    frame_count = 2 # Adjust as necessary
    for i in range(frame_count):
        file_name = f'frame{str(i+1).zfill(3)}.pdf'
        assert os.path.exists(file_name)

        if has_invisible_text(file_name):
            invisible_texts_found += 1

    # The test will fail if both PDFs don't have invisible text.
    assert invisible_texts_found > 0, "No invisible text detected in any of the PDFs"

@pytest.mark.run(order=4)
def test_subprocess_text_only_pdf():
    subprocess_text_only_pdf()
    assert os.path.exists('combine-text.pdf')



# 3. Testing the merging of PDFs
@pytest.mark.run(order=5)
def test_merge():
    merge('combine-text.pdf', 'combine-img.pdf', basename + '.pdf')
    assert os.path.exists(f'{basename}.pdf')



# 4. Testing removal of temporary files
@pytest.mark.run(order=6)
def test_subprocess_remove_temp_files():
    subprocess_remove_temp_files()
    assert not os.path.exists('frame000.png')
    assert not os.path.exists('frame001.pdf')
    assert not os.path.exists('combine-img.pdf')



def has_invisible_text(pdf_path):
    """
    Check the PDF for invisible text using PyPDF2.
    """
    pdf_path = os.path.join(os.getcwd(), pdf_path)

    # Extract text using PyPDF2
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()

    # If the output text is non-empty, we assume there's invisible text in the PDF
    return bool(extracted_text.strip())