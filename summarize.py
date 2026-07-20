import sys
import json
import urllib.request
import os

# ponytail: Stdlib urllib + stdlib json. No extra HTTP frameworks needed. YAGNI.

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (P2P-Summarizer)'})
    try:
        # ponytail: 10s socket timeout prevents indefinite hangs on stalled remote endpoints.
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Network error fetching {url}: {e}")
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
    pdb_data = json.loads(fetch(pdb_url))
    
    # ponytail: Safe dict traversal prevents KeyError crashes if primary citation is missing.
    citation = pdb_data.get('rcsb_primary_citation') or {}
    pmid = citation.get('pdbx_database_id_PubMed')
    title = (pdb_data.get('struct') or {}).get('title', f"Structure {pdb_id}")

    if not pmid:
        print(f"⚠️ No PubMed primary citation linked in PDB entry {pdb_id}.")
        sys.exit(1)

    print(f"Found PubMed ID {pmid}. Fetching abstract from NCBI...")
    ncbi_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=text&rettype=abstract"
    abstract_text = fetch(ncbi_url)

    print("Sending to NVIDIA NIM for summarization...")
    from openai import OpenAI
    
    # ponytail: Accept NVIDIA_API_KEY or NVIDIA_NIM_API_KEY seamlessly.
    api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")
    if not api_key:
        print("❌ Error: Set NVIDIA_API_KEY or NVIDIA_NIM_API_KEY in your environment.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
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

    print("\n--- SUMMARY ---\n", flush=True)
    print(response.choices[0].message.content or "(No response generated)", flush=True)

if __name__ == "__main__":
    main()
