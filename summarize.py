import sys
import json
import urllib.request
import os

# ponytail: No complex agent frameworks. Just grab the data synchronously and dump it into the prompt. YAGNI.

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (P2P-Summarizer)'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Network error: {e}")
        sys.exit(1)

def main():
    # Force UTF-8 output to prevent Windows charmap errors when printing emojis
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: uv run summarize.py <PDB_ID>")
        sys.exit(1)

    pdb_id = sys.argv[1].upper()
    
    print(f"Fetching PDB metadata for {pdb_id}...")
    pdb_url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
    pdb_data_raw = fetch(pdb_url)
    pdb_data = json.loads(pdb_data_raw)
    
    try:
        # Navigate the PDB JSON to find the primary PubMed ID
        pmid = pdb_data['rcsb_primary_citation']['pdbx_database_id_PubMed']
        title = pdb_data['struct']['title']
    except KeyError:
        print("Could not find a primary citation or title in PDB for this structure.")
        sys.exit(1)

    print(f"Found PubMed ID {pmid}. Fetching abstract from NCBI...")
    ncbi_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=text&rettype=abstract"
    abstract_text = fetch(ncbi_url)

    print("Sending to NVIDIA NIM for summarization...")
    from openai import OpenAI
    
    # NVIDIA NIM uses the standard OpenAI API specification
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_API_KEY")
    )
    
    prompt = f"""
    You are a structural biology assistant. 
    Here is data for PDB ID {pdb_id}:
    
    Title: {title}
    
    PubMed Abstract:
    {abstract_text}
    
    Make the summary highly engaging, visual, and interesting for a CLI output. Do the following:
    1. Give it a catchy title with emojis.
    2. Provide a 2-sentence TL;DR.
    3. Draw a simple ASCII art diagram showing how the proteins interact based on the abstract (e.g., Antibody -> Virus, or Enzyme -> Substrate).
    4. Create a clean Markdown table summarizing: The Main Protein, Its Target/Function, and The "Aha!" Discovery in this paper.
    """

    response = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    print("\n--- SUMMARY ---\n")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
