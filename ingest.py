import sys
import json
import urllib.request
import os
from datetime import datetime, timedelta

# ponytail: Simple ingestion + triage script. Stdlib + NVIDIA NIM (8B). YAGNI.

def fetch_json(url, data=None):
    headers = {'User-Agent': 'Mozilla/5.0 (P2P-Summarizer)', 'Content-Type': 'application/json'}
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    else:
        req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (P2P-Summarizer)'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching text {url}: {e}")
        return ""

def search_recent_pdbs(days=7, limit=15):
    """Fetch PDB IDs released or deposited in the last N days."""
    date_cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    print(f"🔍 Searching RCSB PDB for entries since {date_cutoff}...")
    
    query_payload = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_accession_info.initial_release_date",
                "operator": "greater_or_equal",
                "value": date_cutoff
            }
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": limit},
            "sort": [{"sort_by": "rcsb_accession_info.initial_release_date", "direction": "desc"}]
        }
    }
    
    res = fetch_json("https://search.rcsb.org/rcsbsearch/v2/query", data=query_payload)
    if res and "result_set" in res:
        pdb_ids = [item["identifier"] for item in res["result_set"]]
        print(f"✅ Found {len(pdb_ids)} PDB entries: {', '.join(pdb_ids[:5])}...")
        return pdb_ids
    
    print("⚠️ No entries found with release date query, falling back to deposit date search...")
    query_payload["query"]["parameters"]["attribute"] = "rcsb_accession_info.deposit_date"
    res = fetch_json("https://search.rcsb.org/rcsbsearch/v2/query", data=query_payload)
    if res and "result_set" in res:
        return [item["identifier"] for item in res["result_set"]]
    
    return []

def get_pdb_details(pdb_id):
    """Fetch title & PubMed abstract for a PDB ID."""
    pdb_data = fetch_json(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}")
    if not pdb_data:
        return None
    
    try:
        title = pdb_data.get('struct', {}).get('title', 'Unknown Title')
        pmid = pdb_data.get('rcsb_primary_citation', {}).get('pdbx_database_id_PubMed')
        
        abstract = ""
        if pmid:
            ncbi_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=text&rettype=abstract"
            abstract = fetch_text(ncbi_url)
            
        return {
            "pdb_id": pdb_id,
            "title": title,
            "pmid": pmid,
            "abstract": abstract
        }
    except Exception as e:
        print(f"Error parsing details for {pdb_id}: {e}")
        return None

def triage_structure(client, pdb_info):
    """Use Llama 3.1 8B via NVIDIA NIM to rate and triage the structure."""
    prompt = f"""
You are a structural biology editor selecting papers for a "Proteins of the Week" newsletter.
Evaluate this structure:

PDB ID: {pdb_info['pdb_id']}
Title: {pdb_info['title']}
Abstract: {pdb_info['abstract'][:1500] if pdb_info['abstract'] else 'No abstract available.'}

Rate its interest, novelty, and clinical/biological relevance on a scale of 1 to 10.
Return ONLY valid JSON with keys:
"score": <number 1-10>,
"reason": "<one short sentence reason>",
"passed": <boolean true if score >= 7 else false>
"""
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        # Clean potential markdown wrapping
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        return result
    except Exception as e:
        print(f"⚠️ Triage failed for {pdb_info['pdb_id']}: {e}")
        return {"score": 5, "reason": "Triage evaluation failed", "passed": False}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("❌ Error: NVIDIA_API_KEY environment variable not set.")
        sys.exit(1)
        
    from openai import OpenAI
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    
    pdb_ids = search_recent_pdbs(days=7, limit=10)
    if not pdb_ids:
        print("No recent PDBs found.")
        sys.exit(0)

    print(f"\n🧪 Triaging {len(pdb_ids)} structures with Llama 3.1 8B...\n")
    triaged_list = []
    
    for pid in pdb_ids:
        print(f"➡️ Processing {pid}...", end=" ", flush=True)
        details = get_pdb_details(pid)
        if not details:
            print("Failed to fetch details.")
            continue
            
        triage = triage_structure(client, details)
        details["score"] = triage.get("score", 0)
        details["reason"] = triage.get("reason", "")
        details["passed"] = triage.get("passed", False)
        
        status = "✅ PASSED" if details["passed"] else "❌ REJECTED"
        print(f"{status} (Score: {details['score']}/10) - {details['reason']}")
        
        if details["passed"]:
            triaged_list.append(details)
            
    # Sort passed structures by score descending
    triaged_list.sort(key=lambda x: x["score"], reverse=True)
    
    output_file = "triaged_pdbs.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(triaged_list, f, indent=2)
        
    print(f"\n🎉 Done! Saved {len(triaged_list)} high-impact structures to {output_file}")

if __name__ == "__main__":
    main()
