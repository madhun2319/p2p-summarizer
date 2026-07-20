import sys
import json
import os
from datetime import datetime

# ponytail: Newsletter generator configured for Top 5 triaged PDB structures. YAGNI.

def generate_70b_summary(client, pdb_item):
    pdb_id = pdb_item['pdb_id']
    title = pdb_item['title']
    abstract_text = pdb_item.get('abstract', '')
    
    context = f"Title: {title}\n"
    if abstract_text:
        context += f"\nPubMed Abstract:\n{abstract_text[:1200]}"
    else:
        context += "\n(No PubMed abstract attached to this structural deposit yet)."
    
    prompt = f"""
You are a structural biology editor writing for a top-tier science newsletter.
Here is data for PDB ID {pdb_id}:

{context}

Make the summary highly engaging, visual, and concise for a newsletter issue.
Do the following:
1. Give it a catchy headline with emojis.
2. Provide a 2-sentence TL;DR.
3. Draw a simple ASCII art diagram showing how the proteins interact or function based on the data.
4. Create a clean Markdown table summarizing:
   | Attribute | Details |
   |---|---|
   | Main Protein | ... |
   | Target / Function | ... |
   | Key Discovery | ... |
"""
    try:
        # ponytail: timeout is set on the client, not per-call. Removed invalid kwarg.
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=450,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Error generating 70B summary for {pdb_id}: {e}", flush=True)
        return f"### 🧬 {pdb_id}: {title}\n\n**TL;DR:** High-impact structure identified in weekly triage.\n"

def build_newsletter(summaries):
    date_str = datetime.now().strftime("%B %d, %Y")
    file_date = datetime.now().strftime("%Y_%m_%d")
    
    header = f"""# 🧬 Proteins of the Week — Top 5 Highlights ({date_str})
*Curated & Automated Structural Biology Highlights*

---

"""
    body = "\n\n---\n\n".join(summaries)
    
    footer = """

---
*Generated automatically by P2P Summarizer Engine (NVIDIA NIM Llama-3.1-70B & 8B).*
"""
    markdown_content = header + body + footer
    
    md_filename = f"newsletter_{file_date}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    abs_path = os.path.abspath(md_filename).replace('\\', '/')
    print(f"✅ Saved Newsletter ({len(summaries)} entries): [file:///{abs_path}]", flush=True)
    return md_filename

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    triaged_file = "triaged_pdbs.json"
    if not os.path.exists(triaged_file):
        print(f"❌ Error: {triaged_file} not found. Please run ingest.py first.", flush=True)
        sys.exit(1)
        
    with open(triaged_file, "r", encoding="utf-8") as f:
        items = json.load(f)
        
    # Take top 5 triaged items
    top_items = items[:5]
    if not top_items:
        print("ℹ️ No triaged items found.", flush=True)
        sys.exit(0)
        
    api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")
    if not api_key:
        print("❌ Error: Set NVIDIA_API_KEY or NVIDIA_NIM_API_KEY in your environment.", flush=True)
        sys.exit(1)
        
    from openai import OpenAI
    # ponytail: Set timeout on the client constructor where the SDK actually supports it.
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key, timeout=30.0)
    
    print(f"📰 Generating Top {len(top_items)} Newsletter Issue using Llama 3.1 70B...\n", flush=True)
    summaries = []
    
    for idx, item in enumerate(top_items, 1):
        print(f"✍️ Summarizing Top {idx}/{len(top_items)} ({item['pdb_id']})...", flush=True)
        summary = generate_70b_summary(client, item)
        summaries.append(summary)

    # ponytail: Build once at the end, not inside the loop.
    md_file = build_newsletter(summaries)
    print(f"\n🎉 Newsletter issue complete! ({md_file})", flush=True)

if __name__ == "__main__":
    main()
