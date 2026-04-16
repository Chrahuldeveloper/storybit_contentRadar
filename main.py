from bs4 import BeautifulSoup
from supabase import create_client
# from sentence_transformers import SentenceTransformer
import numpy as np
# from pytrends.request import TrendReq
# from google import genai
import os
import re
import requests
import asyncio
# import schedule
# import time
from dotenv import load_dotenv

load_dotenv()
gnews_key = os.getenv("GnewsApi")
newsdata_api_key = os.getenv("Newsdata_api_key")

url= os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# model = None

# def get_model():
#     global model
#     if model is None:
#         print("📦 Loading embedding model...")
#         model = SentenceTransformer('all-MiniLM-L6-v2')
#     return model


bbc = "https://www.bbc.com/"

Hf_token = os.getenv("Hf_token")

print(Hf_token)

async def ai_itellengence(article):
    print("ai ready (DeepSeek)")

    url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {Hf_token}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are an expert Viral Content Strategist + Startup Idea Generator.

    News Title:
    {article.get("tittle")}

    STEP 0: VELOCITY SCORE (0-100)
    - If <50 → respond ONLY "SKIP"

    STEP 1: VIRAL CONTENT
    1. Score
    2. 3 Hooks (Negative, Curiosity, Value)
    3. Emotion + why it spreads
    4. Script (0-30s format)
    5. 5 Hashtags

    STEP 2: STARTUP IDEA (ONE LINE ONLY)
    Format:
    Idea: <name> | What: <what> | Users: <users> | Why: <reason>

    Keep output clean and structured.
    """

    data = {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "messages": [
            {"role": "system", "content": "You generate viral content + startup ideas."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=data)

        output = res.json()["choices"][0]["message"]["content"]

        if output.strip() == "SKIP":
            print("Skipped:", article.get("tittle"))
            return

        data = {
            "tittle": article.get("tittle"),
            "summary": output
        }

        supabase.table("content_radar").upsert(
            data,
            on_conflict="tittle"
        ).execute()

        print(output)
        print("Saved: DeepSeek")

        return {"response": output}

    except Exception as e:
        print("DeepSeek error:", e)



def clean_keywords(text):
    stop_words = {
    "the","is","a","an","in","on","at","to","and","but","says",
    "did","not","was","were","of","for","with","by","as","from","this","that",
    "it", "its", "they", "them", "their", "who", "which", "what", "where", "when",
    "how", "why", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "too", "very", "can", "will", "just", "should",
    "now", "about", "after", "before", "during", "under", "over", "between", 
    "into", "through", "breaking", "latest", "report", "update", "watch",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
    "her", "hers", "herself", "about", "against", "between", "into", "through", 
    "during", "before", "after", "above", "below", "up", "down", "out", "off", 
    "over", "under", "again", "further", "then", "once"
    "today", "yesterday", "tomorrow", "daily", "weekly", "month", "year", "years", 
    "time", "days", "hours", "minutes", "new", "old", "first", "last", "next", 
    "recent", "past",
    "report", "reports", "reported", "breaking", "update", "latest", "exclusive", 
    "official", "source", "sources", "according", "confirmed", "told", "claims", 
    "claimed", "details", "video", "watch", "live", "shared", "posted",
    "it", "its", "they", "them", "their", "who", "whom", "which", "what", "where", 
    "when", "how", "why", "all", "any", "both", "each", "few", "more", "most", 
    "other", "some", "such", "no", "nor", "too", "very", "can", "will", "just", 
    "should", "now"
       
   }

    words = re.findall(r"[a-zA-Z]+", text.lower())

    keywords = [w for w in words if w not in stop_words]

    return keywords[:5]



async def calculate_cos(article):
    try:
        await ai_itellengence(article=article)
        print("ai answer saved")

        await asyncio.sleep(2)

    except Exception as e:
        print("Processing error:", e)

        await asyncio.sleep(5)
        try:
            await ai_itellengence(article=article)
        except Exception as e:
            print("Retry failed:", e)


async def getting_and_scroing_articles(article):
    await calculate_cos(article=article)


# def cosine_similarity(a,b):
#     a = np.array(a)
#     b = np.array(b)
#     return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

async def scrape(url, section_container, inner_section, element, id):

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    if id:
        return

    content = soup.find(section_container, class_=inner_section)

    headlines = content.find_all(element)

    # res = supabase.table("news").select("Vectors").execute()

    # existing_vectors = []

    # for row in res.data:
    #     vec = row.get("Vectors")
    #     if vec:
    #         existing_vectors.append(vec)

    # print(f"Loaded {len(existing_vectors)} existing embeddings")

    for title in headlines:

        text = title.get_text(strip=True)

        if not text:
            continue

        # embedding = get_model().encode(text).tolist()

        is_duplicate = False

        # for vec in existing_vectors:
        #     try:
        #         score = cosine_similarity(embedding, vec)

        #         if score > 0.85:
        #             print("Duplicate skipped:", text)
        #             is_duplicate = True
        #             break
        #     except:
        #         continue

        # if is_duplicate:
        #     continue

        article = {
            "tittle": text,
            # "Vectors": embedding
        }

        try:
            supabase.table("news").upsert(article, on_conflict="tittle").execute()
            print("Saved:", text)
            # existing_vectors.append(embedding)
            await getting_and_scroing_articles(article)
        except Exception as e:
            print("Failed:", text)
            print(e)

        print("-" * 80)



async def get_data_via_api():

    articles = []
    res = requests.get(f"https://newsdata.io/api/1/latest?apikey={newsdata_api_key}")
    data = res.json()

    for item in data.get("results", []):

        if not isinstance(item, dict):
            continue

        title = item.get("tittle")   

        if not title:
            continue

        # embedding = get_model().encode(title).tolist()

        articles.append({
            "tittle": title,
            # "Vectors": embedding
        })

    res2 =  requests.get(
        f"https://gnews.io/api/v4/search?q=example&lang=en&country=in&max=10&apikey={gnews_key}"
    )
    data2 = res2.json()

    for item in data2.get("articles", []):

        if not isinstance(item, dict):
            continue

        title = item.get("title")  

        if not title:
            continue

        # embedding = get_model().encode(title).tolist()

        articles.append({
            "tittle": title,
            # "Vectors": embedding   
        })
    # res_db = supabase.table("news").select("Vectors").execute()

    # existing_vectors = [
    #     row["Vectors"]
    #     for row in res_db.data
    #     if row.get("Vectors")
    # ]

    # THRESHOLD = 0.85

    for article in articles:

        try:
            # embedding = article["Vectors"]

            is_duplicate = False

            # for vec in existing_vectors:
            #     try:
            #         score = cosine_similarity(embedding, vec)

            #         if score > THRESHOLD:
            #             print("Duplicate skipped:", article["tittle"])
            #             is_duplicate = True
            #             break
            #     except:
            #         continue

            # if is_duplicate:
            #     continue

            supabase.table("news").upsert(article, on_conflict="tittle").execute()

            print("Saved:", article["tittle"])

            # existing_vectors.append(embedding)
            await getting_and_scroing_articles(article)
            
        except Exception as e:
            print("Failed:", article["tittle"])
            print(e)



bbc = "https://www.bbc.com/"

async def cycle():
    print("🚀 Running API fetch...")
    await get_data_via_api()

    print("🧹 Running scrape...")
    await scrape(
        bbc,
        section_container='div',
        inner_section='sc-cd6075cf-0 cJhFtM',
        element='p',
        id=False
    )


async def main():
    while True:
        try:
            await cycle()
            print("✅ Cycle complete")

        except Exception as e:
            print("❌ Cycle error:", e)

        await asyncio.sleep(3600) 


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    asyncio.run(main())