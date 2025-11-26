# Use the official PyLucene image
FROM coady/pylucene:latest

# Install Jupyter Notebook and useful Python packages
RUN pip install jupyter pandas numpy lupyne[graphql,rest]

# Set working directory
WORKDIR /workspace

# Copy files from the build context (lucene_indexer directory)
COPY mydata.csv /workspace/data/mydata.csv

# Copy the Jupyter Notebook file
COPY lupyne_borzik.ipynb /workspace/lupyne_borzik.ipynb

# Expose Jupyter Notebook port
EXPOSE 8888

# Start Jupyter Notebook when container runs
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''"]
