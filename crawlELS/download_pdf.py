import subprocess
import os



def download_pdf(file_link, product_number):
    # Ensure the target directory exists
    os.makedirs('./materials', exist_ok=True)

    # Run the 'curl' command and capture its output
    result = subprocess.run(f'curl {file_link} -o ./materials/{product_number}.pdf', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Print the output and error (if any)
# print(result.stdout)
# print(result.stderr)
