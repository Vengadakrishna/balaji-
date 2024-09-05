## Steps to Get Started

### 1. Clone the Repository

1. Open your terminal or command prompt.
2. Run the following command to clone the repository:

    ```bash
    git clone https://github.com/your-username/your-repository.git
    ```

3. Navigate to the directory where you cloned the repository. For example:

    ```bash
    cd your-repository
    ```

### 2. Install Dependencies

1. Ensure you have Python installed on your system.
2. In the terminal, run the following command to install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

### 3. Check Environment Variables

1. Make sure the environment variables are in the same directory as your project. These variables are necessary for the application to run correctly.

### 4. Use the Endpoint

1. To process a file, you need to access the following endpoint:
   here is the example directory C:\\folder1\\folder_inside_folder 1\\text.pdf

    ```
    http://0.0.0.0:8008/process?file_path=the_file_path\\file.pdf
    ```

3. You can use `curl` to send a request to this endpoint.

    **Using `curl`:**

    ```bash
    curl "http://0.0.0.0:8008/process?file_path=thefilepath\\file.pdf"
    ```
4. localhost url
    ```url
    http://localhost:8008/process?file_path=
    ```
    file path should be in form of ```c: r\\folder 1\\folder 2\\ test.pdf```
