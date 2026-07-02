"""
Science, Chemistry, and Medical Research Skill for Nova
Provides direct, high-performance wrappers for PubChem, PubMed, arXiv, and OpenFDA.
Written completely from scratch using standard HTTP requests.
"""

import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import re
import logging

# Initialize logger
logger = logging.getLogger("nova.science")

def _http_get_json(url):
    """Helper to perform HTTP GET and parse JSON response safely."""
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NovaScienceSkill/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"HTTP GET JSON failed for {url}: {e}")
        return None

def _http_get_xml(url):
    """Helper to perform HTTP GET and parse XML response safely."""
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NovaScienceSkill/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        logger.error(f"HTTP GET XML failed for {url}: {e}")
        return None

# ==========================================
# 1. PubChem Chemistry Database
# ==========================================

def cmd_pubchem(args):
    """
    Usage: pubchem <compound_name> or chemical <compound_name>
    Queries the PubChem PUG-REST API for molecular properties, formula, structure, and weight.
    """
    compound = args.lower().replace("pubchem", "").replace("chemical", "").replace("compound", "").replace("properties of", "").strip()
    if not compound:
        return "Which chemical compound or molecule would you like me to look up? Try saying 'pubchem aspirin'. 🧪"

    print(f"🧪 Querying PubChem database for: {compound}...")
    
    # 1. Resolve compound to properties
    escaped_name = urllib.parse.quote(compound)
    prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{escaped_name}/property/Title,MolecularFormula,MolecularWeight,CanonicalSMILES,XLogP,TPSA,CID/JSON"
    
    data = _http_get_json(prop_url)
    if not data or "PropertyTable" not in data or "Properties" not in data["PropertyTable"]:
        return f"Hmm, I couldn't find a compound named '{compound}' in the PubChem chemistry database. 🧪"

    props = data["PropertyTable"]["Properties"][0]
    cid = props.get("CID")
    title = props.get("Title", compound.title())
    formula = props.get("MolecularFormula", "N/A")
    weight = props.get("MolecularWeight", "N/A")
    smiles = props.get("CanonicalSMILES", "N/A")
    xlogp = props.get("XLogP", "N/A")
    tpsa = props.get("TPSA", "N/A")

    # 2. Try fetching a brief description/pharmacology if available
    desc_text = ""
    if cid:
        desc_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON"
        desc_data = _http_get_json(desc_url)
        if desc_data and "InformationList" in desc_data and "Information" in desc_data["InformationList"]:
            for info in desc_data["InformationList"]["Information"]:
                if "Description" in info:
                    desc_text = info["Description"]
                    break

    # Build response
    response = f"🧪 **Chemical Profile: {title}** (CID: {cid})\n\n"
    if desc_text:
        response += f"{desc_text}\n\n"
        
    response += f"• **Molecular Formula:** {formula}\n"
    response += f"• **Molecular Weight:** {weight} g/mol\n"
    response += f"• **XLogP (Octanol-Water Partition):** {xlogp}\n"
    response += f"• **TPSA (Polar Surface Area):** {tpsa} Å²\n"
    response += f"• **Canonical SMILES:** `{smiles}`\n\n"
    response += f"🖼️ [View 2D Structure](https://pubchem.ncbi.nlm.nih.gov/image/imagegenerator.cgi?cid={cid}&width=300&height=300)\n"

    # Return structured data for the UI/agents
    return {
        "response": response,
        "data": {
            "type": "chemical_profile",
            "cid": cid,
            "title": title,
            "formula": formula,
            "weight": weight,
            "smiles": smiles,
            "xlogp": xlogp,
            "tpsa": tpsa,
            "structure_url": f"https://pubchem.ncbi.nlm.nih.gov/image/imagegenerator.cgi?cid={cid}&width=300&height=300"
        }
    }

# ==========================================
# 2. PubMed Medical Literature
# ==========================================

def cmd_pubmed(args):
    """
    Usage: pubmed <query> or medical literature <query>
    Searches NCBI PubMed for medical/biological papers.
    """
    query = args.lower().replace("pubmed", "").replace("medical literature", "").replace("medical search", "").replace("search for papers on", "").strip()
    if not query:
        return "What medical or biomedical research topic would you like to search for? Try 'pubmed CRISPR therapy'. 🧬"

    print(f"🧬 Searching PubMed database for: {query}...")
    
    # 1. Search for PMIDs
    escaped_query = urllib.parse.quote(query)
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={escaped_query}&retmode=json&retmax=3"
    
    search_data = _http_get_json(search_url)
    if not search_data or "esearchresult" not in search_data or "idlist" not in search_data["esearchresult"]:
        return f"I couldn't find any medical papers matching '{query}' on PubMed. 🧬"
        
    id_list = search_data["esearchresult"]["idlist"]
    if not id_list:
        return f"No research articles matched '{query}' on PubMed. 🧬"

    # 2. Fetch summaries/abstracts
    ids_str = ",".join(id_list)
    summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
    
    summary_data = _http_get_json(summary_url)
    if not summary_data or "result" not in summary_data:
        return "I found matching article IDs, but failed to retrieve their summaries from PubMed."

    result_dict = summary_data["result"]
    articles = []
    
    response = f"🧬 **PubMed Search Results for '{query.title()}'**\n\n"
    
    count = 1
    for pmid in id_list:
        if pmid in result_dict:
            art = result_dict[pmid]
            title = art.get("title", "No Title")
            authors = ", ".join([a.get("name", "") for a in art.get("authors", [])[:3]])
            pub_date = art.get("pubdate", "N/A")
            source = art.get("source", "PubMed")
            
            articles.append({
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "date": pub_date,
                "source": source,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
            
            response += f"{count}. **{title}**\n"
            response += f"   ◈ Authors: *{authors}* | Date: {pub_date} | Source: *{source}*\n"
            response += f"   🔗 [View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)\n\n"
            count += 1

    return {
        "response": response,
        "data": {
            "type": "pubmed_results",
            "query": query,
            "articles": articles
        }
    }

# ==========================================
# 3. arXiv Scientific Preprints
# ==========================================

def cmd_arxiv(args):
    """
    Usage: arxiv <query> or preprint <query> or paper search <query>
    Searches the arXiv API for physics, mathematics, CS, and biology preprints.
    """
    query = args.lower().replace("arxiv", "").replace("preprint", "").replace("paper search", "").strip()
    if not query:
        return "What scientific research preprint or paper would you like me to find on arXiv? Try 'arxiv artificial intelligence'. 🌌"

    print(f"🌌 Searching arXiv database for: {query}...")
    
    escaped_query = urllib.parse.quote(query)
    arxiv_url = f"http://export.arxiv.org/api/query?search_query=all:{escaped_query}&max_results=3"
    
    xml_data = _http_get_xml(arxiv_url)
    if not xml_data:
        return f"I couldn't fetch any papers for '{query}' from arXiv at this time."

    try:
        # Standard XML Parsing
        root = ET.fromstring(xml_data)
        
        # Namespaces are usually in the form of {http://www.w3.org/2005/Atom}
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        
        if not entries:
            return f"I couldn't find any preprints matching '{query}' on arXiv. 🌌"
            
        papers = []
        response = f"🌌 **arXiv Preprint Results for '{query.title()}'**\n\n"
        
        for idx, entry in enumerate(entries, 1):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            if len(summary) > 220:
                summary = summary[:220] + "..."
                
            published = entry.find('atom:published', ns).text[:10]
            
            # Authors list
            authors = [auth.find('atom:name', ns).text for auth in entry.findall('atom:author', ns)]
            authors_str = ", ".join(authors[:3])
            
            # Retrieve PDF Link
            pdf_url = ""
            for link in entry.findall('atom:link', ns):
                if link.attrib.get('title') == 'pdf' or link.attrib.get('type') == 'application/pdf':
                    pdf_url = link.attrib.get('href', '')
                    break
            
            if not pdf_url:
                # Fallback to the ID URL
                pdf_url = entry.find('atom:id', ns).text
                
            papers.append({
                "title": title,
                "summary": summary,
                "authors": authors_str,
                "date": published,
                "pdf_url": pdf_url
            })
            
            response += f"{idx}. **{title}**\n"
            response += f"   ◈ Authors: *{authors_str}* | Published: {published}\n"
            response += f"   ◈ Abstract: *{summary}*\n"
            response += f"   🔗 [Download PDF]({pdf_url})\n\n"

        return {
            "response": response,
            "data": {
                "type": "arxiv_results",
                "query": query,
                "papers": papers
            }
        }
    except Exception as e:
        logger.error(f"Error parsing arXiv XML: {e}")
        return "I encountered a problem parsing the preprint summaries from arXiv."

# ==========================================
# 4. OpenFDA Drug Database
# ==========================================

def cmd_openfda(args):
    """
    Usage: openfda <drug_name> or drug info <drug_name>
    Searches the official FDA OpenAPI for ingredients, warnings, and drug labels.
    """
    drug = args.lower().replace("openfda", "").replace("drug info", "").replace("fda info", "").strip()
    if not drug:
        return "Which prescription or over-the-counter drug would you like me to look up? Try 'openfda ibuprofen'. 💊"

    print(f"💊 Searching FDA database for: {drug}...")
    
    escaped_drug = urllib.parse.quote(drug)
    fda_url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{escaped_drug}&limit=1"
    
    data = _http_get_json(fda_url)
    if not data or "results" not in data:
        # Fallback to general generic search if brand name lookup fails
        fda_url = f"https://api.fda.gov/drug/label.json?search={escaped_drug}&limit=1"
        data = _http_get_json(fda_url)
        if not data or "results" not in data:
            return f"I couldn't find any FDA records for the drug '{drug}'. 💊"

    result = data["results"][0]
    
    # Extract details with fallbacks
    openfda = result.get("openfda", {})
    brand_name = openfda.get("brand_name", [drug.title()])[0]
    generic_name = openfda.get("generic_name", ["N/A"])[0]
    manufacturer = openfda.get("manufacturer_name", ["N/A"])[0]
    
    purpose = result.get("purpose", ["N/A"])[0]
    active_ingredient = result.get("active_ingredient", ["N/A"])[0]
    warnings = result.get("warnings", ["N/A"])[0]
    indications = result.get("indications_and_usage", ["N/A"])[0]
    dosage = result.get("dosage_and_administration", ["N/A"])[0]

    # Limit warning length for neat presentation
    if len(warnings) > 350:
        warnings = warnings[:350] + "..."

    response = f"💊 **FDA Drug Profile: {brand_name}**\n"
    response += f"◈ Generic Name: *{generic_name}* | Manufacturer: *{manufacturer}*\n\n"
    response += f"• **Purpose:** {purpose}\n"
    response += f"• **Active Ingredient:** {active_ingredient}\n"
    response += f"• **Indications & Usage:** {indications}\n"
    response += f"• **Dosage & Administration:** {dosage}\n"
    response += f"• **⚠️ Boxed Warnings:** {warnings}\n"

    return {
        "response": response,
        "data": {
            "type": "fda_drug_profile",
            "brand_name": brand_name,
            "generic_name": generic_name,
            "purpose": purpose,
            "warnings": warnings
        }
    }

# ==========================================
# Skill Registration Hook
# ==========================================

def register(dispatcher):
    # PubChem
    dispatcher.register("pubchem", cmd_pubchem)
    dispatcher.register("chemical", cmd_pubchem)
    dispatcher.register("compound", cmd_pubchem)
    
    # PubMed
    dispatcher.register("pubmed", cmd_pubmed)
    dispatcher.register("medical literature", cmd_pubmed)
    dispatcher.register("medical search", cmd_pubmed)
    
    # arXiv
    dispatcher.register("arxiv", cmd_arxiv)
    dispatcher.register("preprint", cmd_arxiv)
    dispatcher.register("paper search", cmd_arxiv)
    
    # OpenFDA
    dispatcher.register("openfda", cmd_openfda)
    dispatcher.register("drug info", cmd_openfda)
    dispatcher.register("fda info", cmd_openfda)
