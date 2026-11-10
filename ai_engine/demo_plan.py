from __future__ import annotations
from typing import Any
from ai_engine.topic_classifier import classify_topic

def build_demo_plan(topic: str, duration_seconds: int = 70) -> dict[str, Any]:
    clean = topic.strip() or "Two Sum"
    profile = classify_topic(clean)
    if profile.family == "dsa" and "two" in clean.lower() and "sum" in clean.lower():
        beats = [
          dict(
            id="hook",
            type="kinetic_title",
            title="TWO SUM",
            spoken_text="Interview mein Two Sum pucha toh 90 percent log brute force bolte hain, aur interviewer wahi reject kar deta hai!",
            visual_action="Reveal hook question with high-stakes dilemma card.",
            accent_words=["Two Sum", "reject"],
            nodes=[], connections=[], steps=[]
          ),
          dict(
            id="problem",
            type="concept_visual",
            title="THE PROBLEM",
            spoken_text="Kyunki agar array mein 10,000 numbers hain, toh nested loops 10 crore comparisons karenge! Hamein chahiye O of n single pass.",
            visual_action="Show array cards and highlight the target 9.",
            accent_words=["10 crore", "O(n)"],
            nodes=[{"label":"2","detail":"Index 0"},{"label":"7","detail":"Index 1"},{"label":"9","detail":"Target"}],
            connections=[[0,1],[0,2],[1,2]],
            steps=[]
          ),
          dict(
            id="baseline",
            type="comparison",
            title="BRUTE FORCE vs OPTIMAL",
            spoken_text="Brute force har pair ko baar-baar compare karta hai — O of n square! Lekin smart approach mein hum aage nahi, peeche dekhte hain.",
            visual_action="Compare brute force O(n²) with optimal O(n).",
            accent_words=["O(n²)", "single pass"],
            nodes=[{"label":"Outer loop","detail":"Pick one number"},{"label":"Inner loop","detail":"Check remaining numbers"}],
            connections=[],
            steps=[]
          ),
          dict(
            id="idea",
            type="metric_callout",
            title="THE KEY IDEA",
            spoken_text="Idea simple hai: Target 9 hai, aap 2 par ho. Aage kya dhoondhna hai? Exactly 7! Target minus current number.",
            visual_action="Show complement equation: 9 minus current equals complement.",
            accent_words=["Target 9", "complement"],
            metric="TARGET − NUM"
          ),
          dict(
            id="hashmap",
            type="architecture_build",
            title="THE DIARY METAPHOR",
            spoken_text="Aage baar-baar dhoondhne ke bajaye, bas ek khali HashMap bana lo — socho yeh aapki memory diary hai jo purane numbers yaad rakhti hai.",
            visual_action="Animate HashMap storing seen elements and instant lookup.",
            accent_words=["HashMap", "memory diary"],
            nodes=[{"label":"HashMap","detail":"Memory diary"},{"label":"Lookup","detail":"Instant O(1)"},{"label":"Insert","detail":"Store seen numbers"}],
            connections=[[0,1],[0,2]]
          ),
          dict(
            id="dryrun",
            type="data_flow",
            title="INTERACTIVE DRY RUN",
            spoken_text="2 aaya, diary mein 7 nahi tha, 2 store kiya. Agla 7 aaya, diary boli: 2 index 0 par hai! Instant answer!",
            visual_action="Step through array indices with instant complement match.",
            accent_words=["2 store", "index 0", "Instant answer"],
            steps=[{"label":"Read 2","detail":"Need 7; diary empty -> store 2"},{"label":"Read 7","detail":"Need 2; diary found at index 0!"},{"label":"Return","detail":"[0, 1] found!"}]
          ),
          dict(
            id="complexity",
            type="comparison",
            title="COMPLEXITY WIN",
            spoken_text="Single loop mein instant lookup! Time complexity O of n square se sidha drop hokar O of n ban gayi.",
            visual_action="Contrast O(n²) time with O(n) linear time.",
            accent_words=["O(n)", "instant lookup"],
            nodes=[{"label":"Time","detail":"O(n) linear"},{"label":"Space","detail":"O(n) map"}]
          ),
          dict(
            id="summary",
            type="summary",
            title="REMEMBER THIS",
            spoken_text="Yaad rakho: Har number ka complement HashMap mein check karo. Comment TWOSUM for complete PDF interview notes!",
            visual_action="Land on the PDF cheatsheet card and follow CTA.",
            accent_words=["complement", "TWOSUM"],
            nodes=[{"label":"Target − Current","detail":"Find complement"},{"label":"HashMap","detail":"Instant lookup"},{"label":"Return","detail":"Pair [0, 1]"}],
            connections=[[0,1],[1,2]]
          )
        ]
    elif "scaling" in clean.lower() or "horizontal" in clean.lower():
        beats = [
          dict(
            id="hook",
            type="kinetic_title",
            title="HORIZONTAL SCALING",
            spoken_text="Interview mein poocha: Traffic badhne par ek bada 128-core server kyun nahi lagate? Horizontal scaling kyun karte hain?",
            tts_text="इंटरव्यू में पूछा: ट्रैफिक बढ़ने पर एक बड़ा 128-core सर्वर क्यों नहीं लगाते? Horizontal scaling क्यों करते हैं?",
            visual_action="Reveal high-stakes scaling dilemma card.",
            accent_words=["Horizontal scaling", "128-core"],
            nodes=[], connections=[], steps=[]
          ),
          dict(
            id="vertical_limits",
            type="comparison",
            title="VERTICAL LIMITS",
            spoken_text="Problem samjho: ek akela server kitna bhi bada ho, crash hua toh poora app down! Aur ek limit ke baad RAM aur CPU badhana namumkin ho jata hai.",
            tts_text="प्रॉब्लम समझो: एक अकेला सर्वर कितना भी बड़ा हो, क्रैश हुआ तो पूरा ऐप डाउन! और एक लिमिट के बाद RAM और CPU बढ़ाना नामुमकिन हो जाता है!",
            visual_action="Compare vertical scaling single point of failure with horizontal cluster.",
            accent_words=["poora app down", "RAM aur CPU"],
            nodes=[{"label": "Vertical Scaling", "detail": "Single Point of Failure"}, {"label": "Horizontal Scaling", "detail": "Commodity Server Pool"}],
            connections=[], steps=[]
          ),
          dict(
            id="horizontal_model",
            type="architecture_build",
            title="COMMODITY POOL",
            spoken_text="Isliye ek bade server ke badle hum 3 chhote servers laga dete hain! Isi ko Horizontal Scaling kehte hain — yaani zyada machines jodna.",
            tts_text="इसलिए एक बड़े सर्वर के बदले हम तीन छोटे सर्वर्स लगा देते हैं! इसी को Horizontal Scaling कहते हैं — यानी ज़्यादा मशीन्स जोड़ना!",
            visual_action="Animate load balancer distributing requests across server pool.",
            accent_words=["3 chhote servers", "Horizontal Scaling"],
            nodes=[{"label": "Load Balancer", "detail": "Traffic distribution"}, {"label": "Server A", "detail": "Worker 1"}, {"label": "Server B", "detail": "Worker 2"}, {"label": "Server C", "detail": "Worker 3"}],
            connections=[[0, 1], [0, 2], [0, 3]],
            steps=[]
          ),
          dict(
            id="load_balancer",
            type="data_flow",
            title="THE LOAD BALANCER",
            spoken_text="Inke aage lagta hai Load Balancer! Ye aane wale 1 lakh requests ko Round-Robin se teeno servers mein barabar baant deta hai.",
            tts_text="इनके आगे लगता है Load Balancer! ये आने वाले एक लाख रिक्वेस्ट्स को Round-Robin से तीनों सर्वर्स में बराबर बाँट देता है!",
            visual_action="Show request packets streaming through Nginx load balancer to servers.",
            accent_words=["Load Balancer", "Round-Robin"],
            metric="100K REQ / SEC",
            steps=[{"label": "100K Traffic", "detail": "Incoming client requests"}, {"label": "Round Robin", "detail": "Even split 33% each"}, {"label": "3x Workers", "detail": "Parallel processing"}]
          ),
          dict(
            id="fault_tolerance",
            type="concept_visual",
            title="ZERO DOWNTIME",
            spoken_text="Sabse bada fayda? Agar Server 2 achanak crash bhi ho jaye, toh Load Balancer 1 second mein sara traffic Server 1 aur 3 pe bhej deta hai — Zero Downtime!",
            tts_text="सबसे बड़ा फ़ायदा? अगर Server 2 अचानक क्रैश भी हो जाए, तो Load Balancer एक सेकंड में सारा ट्रैफिक Server 1 और 3 पे भेज देता है — Zero Downtime!",
            visual_action="Server 2 turns red/crashed while traffic seamlessly flows to Server 1 and 3.",
            accent_words=["Zero Downtime", "1 second"],
            metric="99.999% UPTIME",
            nodes=[{"label": "Server 2 Crash", "detail": "Health check fail"}, {"label": "Auto Reroute", "detail": "50% to A, 50% to C"}],
            connections=[]
          ),
          dict(
            id="stateless",
            type="metric_callout",
            title="STATELESS WORKERS",
            spoken_text="Par ek zaroori rule hai: Servers ko Stateless rakhna padta hai! User ka login session server ki memory mein nahi, balki bahar Redis ya Database mein save hota hai.",
            tts_text="पर एक ज़रूरी रूल है: सर्वर्स को Stateless रखना पड़ता है! यूज़र का लॉगिन सेशन सर्वर की मेमोरी में नहीं, बल्कि बाहर Redis या Database में सेव होता है!",
            visual_action="Show shared Redis cache and database tier decoupled from app servers.",
            accent_words=["Stateless", "Redis ya Database"],
            metric="STATELESS TIER"
          ),
          dict(
            id="summary",
            type="summary",
            title="SYSTEM DESIGN WIN",
            spoken_text="Vertical matlab bada server, Horizontal matlab zyada servers! Agar Load Balancer khud crash ho jaye toh kya karoge? Comment karo, aur save kar lo — interview mein kaam aayega!",
            tts_text="Vertical मतलब बड़ा सर्वर, Horizontal मतलब ज़्यादा सर्वर्स! अगर Load Balancer ख़ुद क्रैश हो जाए तो क्या करोगे? कमेंट करो, और सेव कर लो — इंटरव्यू में काम आएगा!",
            visual_action="Show PDF cheat sheet card and DM automation CTA.",
            accent_words=["Horizontal matlab zyada servers", "Comment karo"],
            nodes=[{"label": "Load Balancer", "detail": "Traffic distributor"}, {"label": "Stateless Pool", "detail": "Commodity workers"}, {"label": "Shared State", "detail": "Redis / DB cluster"}],
            connections=[[0, 1], [1, 2]]
          )
        ]
    elif "rag" in clean.lower() or "retrieval" in clean.lower() or "vector" in clean.lower():
        beats = [
          dict(
            id="hook",
            type="kinetic_title",
            title="500 PAGE PDF IN 2 SEC",
            spoken_text="Interviewer ne poocha: 500 page ki PDF aur ChatGPT ka jawab 2 second mein kaise? Woh poori PDF padhta hai? Nahi, bas sahi page! Isi ko RAG kehte hain.",
            tts_text="इंटरव्यूअर ने पूछा: पाँच सौ पेज की पी डी एफ, और ChatGPT का जवाब दो सेकंड में कैसे? वो पूरी पी डी एफ पढ़ता है? नहीं, बस सही पेज! इसी को आर ए जी कहते हैं!",
            visual_action="Reveal 500-page Biology PDF stack flipping into 497 unread pages stamp.",
            accent_words=["500 page ki PDF", "497 padhe hi nahi", "RAG"],
            metric="500 PAGES · 2 SEC",
            nodes=[], connections=[], steps=[]
          ),
          dict(
            id="problem",
            type="comparison",
            title="CONTEXT WINDOW OVERLOAD",
            spoken_text="Problem samjho: Zyadatar AI ek baar mein itna bada PDF nahi padh paate — Context Window overload ho jata hai! Aur jo padh paate hain woh 12 second aur 30 rupaye lete hain.",
            tts_text="प्रॉब्लम समझो: ज़्यादातर ए आई एक बार में इतना बड़ा पी डी एफ नहीं पढ़ पाते — Context Window ओवरलोड हो जाता है! और जो पढ़ पाते हैं, वो बारह सेकंड और तीस रुपये लेते हैं!",
            visual_action="Show OVERLOAD warning and BADA AI 300/500 context window limit with 12s / 30 Rs cost.",
            accent_words=["Context Window", "Overload", "12 second"],
            metric="CONTEXT WINDOW 🧠",
            nodes=[
              {"label": "Standard AI (300/500)", "detail": "+200 pages andar nahi aaye · OVERLOAD!"},
              {"label": "Bada AI (500/500)", "detail": "Har sawal pe 500 pages · 12s & ₹30 cost"}
            ],
            connections=[], steps=[]
          ),
          dict(
            id="embeddings",
            type="architecture_build",
            title="CHUNKS & EMBEDDINGS",
            spoken_text="RAG mein pehle PDF ko chhote tukdon mein kaato — inhein Chunks kehte hain! Phir AI Model har chunk ka matlab numbers mein likhta hai — isse Embedding kehte hain!",
            tts_text="आर ए जी में पहले पी डी एफ को छोटे टुकड़ों में काटो — इन्हें Chunks कहते हैं! फिर ए आई मॉडल हर chunk का मतलब नंबर्स में लिखता है — इसे Embedding कहते हैं!",
            visual_action="Slice 500 pages into 2,000 chunks and convert each chunk into [x, y] vector numbers.",
            accent_words=["Chunks", "Embedding", "numbers"],
            metric="500 PAGES → ✂ 2,000 CHUNKS",
            nodes=[
              {"label": "P.12 Cell", "detail": "Vector: [4, 1]", "color": "#58A6FF"},
              {"label": "P.211 Photosynthesis: intro", "detail": "Vector: [9, 8] · Same Topic", "color": "#3FB950"},
              {"label": "P.212 Dhoop + Paani", "detail": "Vector: [9, 9] · Same Topic", "color": "#3FB950"},
              {"label": "P.340 Genetics", "detail": "Vector: [1, 5] · Different", "color": "#FF4D4D"}
            ],
            connections=[[0, 1], [1, 2]],
            steps=[]
          ),
          dict(
            id="retrieval",
            type="data_flow",
            title="VECTOR DB & RETRIEVAL",
            spoken_text="Yeh saare numbers Vector Database mein rakh do. Tumne poocha Photosynthesis kya hai? Vector DB sawal ke numbers [9, 8] ko lakho chunks se milata hai aur sabse paas wale 3 chunks lata hai — yahi Retrieval hai!",
            tts_text="ये सारे नंबर्स Vector Database में रख दो! तुमने पूछा Photosynthesis क्या है? Vector डी बी सवाल के नंबर्स को लाखों chunks से मिलाता है, और सबसे पास वाले तीन chunks लाता है — यही Retrieval है!",
            visual_action="Animate Vector DB Cylinder matching [9, 8] against [9, 9] PAAS vs [1, 5] DOOR.",
            accent_words=["Vector Database", "3 chunks", "Retrieval"],
            metric="R = RETRIEVAL",
            steps=[
              {"label": "? Photosynthesis kya hai?", "detail": "AI Model converts query -> [9, 8]"},
              {"label": "[9, 8] vs [9, 9] P.212", "detail": "Photosynthesis · PAAS ✔ (Matched)"},
              {"label": "[9, 8] vs [1, 5] P.340", "detail": "Genetics · DOOR ✕ (Skipped)"}
            ]
          ),
          dict(
            id="generation",
            type="concept_visual",
            title="AUGMENTED GENERATION",
            spoken_text="Phir yeh 3 pages sawal ke saath jod ke AI ko do — yeh jodna hai Augmented! Aur AI bas inhi 3 pages se jawab likhta hai — yeh hai Generation! Dhoondho, Jodo, Likho — yahi hai RAG!",
            tts_text="फिर ये तीन पेजेस सवाल के साथ जोड़ के ए आई को दो — ये जोड़ना है Augmented! और ए आई बस इन्हीं तीन पेजेस से जवाब लिखता है — ये है Generation! ढूँढो, जोड़ो, लिखो — यही है आर ए जी!",
            visual_action="Show R (Retrieval) + A (Augmented) + G (Generation) pipeline producing exact answer.",
            accent_words=["Augmented", "Generation", "Dhoondho, Jodo, Likho"],
            metric="DHOONDHO · JODO · LIKHO",
            nodes=[
              {"label": "R — Retrieval (Dhoondho)", "detail": "Top 3 chunks from Vector DB (P.211, P.212, P.213)", "color": "#3FB950"},
              {"label": "A — Augmented (Jodo)", "detail": "Query + 3 Pages combined into prompt", "color": "#FF9F2A"},
              {"label": "G — Generation (Likho)", "detail": "AI writes answer from 3 pages in 2 sec!", "color": "#58A6FF"}
            ],
            connections=[[0, 1], [1, 2]],
            steps=[]
          ),
          dict(
            id="summary",
            type="summary",
            title="RAG CHEATSHEET",
            spoken_text="500 nahi, bas 3 pages — isliye 2 second! Par agar jawab 2 chunks ke beech mein kat gaya toh kaise fix karoge? Comment RAG karo, aur save kar lo — interview mein kaam aayega!",
            tts_text="पाँच सौ नहीं, बस तीन पेजेस — इसलिए दो सेकंड! पर अगर जवाब दो chunks के बीच में कट गया तो कैसे फ़िक्स करोगे? कमेंट आर ए जी करो, और सेव कर लो — इंटरव्यू में काम आएगा!",
            visual_action="Show PDF cheat sheet card and DM automation CTA.",
            accent_words=["3 pages", "2 chunks", "Comment RAG"],
            nodes=[{"label": "Chunking & Embedding", "detail": "500 pages -> 2,000 vectors"}, {"label": "Vector Retrieval", "detail": "Top 3 closest chunks [9,8]"}, {"label": "Chunk Overlap", "detail": "Fix boundary cutoffs"}],
            connections=[[0, 1], [1, 2]]
          )
        ]
    elif "consistent" in clean.lower() or "hashing" in clean.lower():
        beats = [
          dict(
            id="hook",
            type="kinetic_title",
            title="CONSISTENT HASHING",
            spoken_text="Interviewer ne poocha: 4 Redis servers mein se 1 crash hua, toh Modulo Hashing se 75 percent cache miss kyun ho jata hai? Jawab hai Consistent Hashing!",
            tts_text="इंटरव्यूअर ने पूछा: चार Redis सर्वर्स में से एक क्रैश हुआ, तो Modulo Hashing से पचहत्तर परसेंट cache miss क्यों हो जाता है? जवाब है Consistent Hashing!",
            visual_action="Reveal 4 Redis nodes where 1 crashes and 75% keys remap.",
            accent_words=["75 percent cache miss", "Consistent Hashing"],
            metric="75% CACHE MISS TRAP",
            nodes=[], connections=[], steps=[]
          ),
          dict(
            id="problem",
            type="comparison",
            title="MODULO N vs HASH RING",
            spoken_text="Problem samjho: Normal hashing mein formula hota hai hash mod N. Jaise hi N 4 se 3 hua, har key ka remainder badal jata hai aur saara traffic Database koTod deta hai!",
            tts_text="प्रॉब्लम समझो: नॉर्मल hashing में फ़ॉर्मूला होता है hash mod N! जैसे ही N चार से तीन हुआ, हर key का remainder बदल जाता है और सारा ट्रैफिक डेटाबेस को तोड़ देता है!",
            visual_action="Compare hash(key) % 4 vs hash(key) % 3 causing 75% key reshuffle.",
            accent_words=["hash mod N", "remainder", "Database"],
            metric="HASH(KEY) % N FAILS",
            nodes=[
              {"label": "Modulo Hashing (hash % N)", "detail": "N=4 -> N=3 shifts 75% of all keys · DB Stampede!"},
              {"label": "Consistent Hashing Ring", "detail": "Only 1/N (25%) keys move · Zero DB overload!"}
            ],
            connections=[], steps=[]
          ),
          dict(
            id="ring_model",
            type="architecture_build",
            title="THE 360° HASH RING",
            spoken_text="Consistent Hashing mein hum linear array nahi, ek 0 se 360 degree ka गोल Hash Ring banate hain! Aur teeno servers ko is ring ki boundary par bitha dete hain.",
            tts_text="Consistent Hashing में हम linear array नहीं, एक ज़ीरो से तीन सौ साठ डिग्री का गोल Hash Ring बनाते हैं! और तीनों सर्वर्स को इस रिंग की बाउंड्री पर बिठा देते हैं!",
            visual_action="Draw 360-degree Hash Ring and place Server S1 (0°), S2 (120°), S3 (240°).",
            accent_words=["360 degree", "Hash Ring"],
            metric="0° — 360° HASH RING",
            nodes=[
              {"label": "Server S1 (0°)", "detail": "Handles arc 240° -> 0°", "color": "#FF9F2A"},
              {"label": "Server S2 (120°)", "detail": "Handles arc 0° -> 120°", "color": "#3FB950"},
              {"label": "Server S3 (240°)", "detail": "Handles arc 120° -> 240°", "color": "#58A6FF"}
            ],
            connections=[[0, 1], [1, 2]],
            steps=[]
          ),
          dict(
            id="clockwise_lookup",
            type="data_flow",
            title="CLOCKWISE KEY ROUTING",
            spoken_text="Ab jab User Key aati hai, uska hash angle nikalo — maan lo 45 degree! Wahan se ghadi ki disha mein yaani Clockwise chalo, jo pehla server mila S2, data wahan save!",
            tts_text="अब जब User Key आती है, उसका hash angle निकालो — मान लो पैंतालीस डिग्री! वहाँ से घड़ी की दिशा में यानी Clockwise चलो, जो पहला सर्वर मिला S2, डेटा वहाँ सेव!",
            visual_action="Animate Key landing at 45° and walking clockwise to Server S2 at 120°.",
            accent_words=["45 degree", "Clockwise", "S2"],
            metric="CLOCKWISE LOOKUP ↻",
            steps=[
              {"label": "1. Hash Key -> 45°", "detail": "Map user_id onto 0°..360° ring"},
              {"label": "2. Walk Clockwise ↻", "detail": "Move forward along the ring arc"},
              {"label": "3. Hit Server S2 (120°)", "detail": "Store & fetch key on first server found!"}
            ],
            nodes=[], connections=[]
          ),
          dict(
            id="virtual_nodes",
            type="concept_visual",
            title="CRASH & VIRTUAL NODES",
            spoken_text="Fayda dekho: Agar S2 crash bhi hua, toh sirf S2 ki keys agle server S3 pe jayengi — baki 75 percent servers untouched! Aur load barabar baantne ke liye hum Virtual Nodes lagate hain.",
            tts_text="फ़ायदा देखो: अगर S2 क्रैश भी हुआ, तो सिर्फ़ S2 की keys अगले सर्वर S3 पे जाएँगी — बाक़ी पचहत्तर परसेंट सर्वर्स untouched! और लोड बराबर बाँटने के लिए हम Virtual Nodes लगाते हैं!",
            visual_action="Show S2 failing and only its keys moving clockwise to S3, plus Virtual Nodes.",
            accent_words=["sirf S2 ki keys", "Virtual Nodes"],
            metric="VIRTUAL NODES (vNODES)",
            nodes=[
              {"label": "1. S2 Crashes", "detail": "Only S2 arc keys shift clockwise to S3", "color": "#FF9F2A"},
              {"label": "2. 75% Keys Untouched", "detail": "S1 and S3 caches remain 100% valid!", "color": "#3FB950"},
              {"label": "3. Virtual Nodes (vNodes)", "detail": "Multiple labels per server for even load", "color": "#58A6FF"}
            ],
            connections=[[0, 1], [1, 2]],
            steps=[]
          ),
          dict(
            id="summary",
            type="summary",
            title="HASHING CHEATSHEET",
            spoken_text="Yaad rakho: 360 degree Hash Ring, Clockwise routing, aur Virtual Nodes! DynamoDB aur Cassandra yahi use karte hain. Comment HASH karo, aur save kar lo — interview mein kaam aayega!",
            tts_text="याद रखो: तीन सौ साठ डिग्री Hash Ring, Clockwise routing, और Virtual Nodes! DynamoDB और Cassandra यही यूज़ करते हैं! कमेंट HASH करो, और सेव कर लो — इंटरव्यू में काम आएगा!",
            visual_action="Show PDF cheat sheet card and DM automation CTA.",
            accent_words=["Hash Ring", "Virtual Nodes", "Comment HASH"],
            nodes=[
              {"label": "360° Hash Ring", "detail": "Servers & keys on same circle"},
              {"label": "Clockwise Walk ↻", "detail": "Only 1/N keys move on crash"},
              {"label": "Virtual Nodes", "detail": "Prevent hot-spots & skew"}
            ],
            connections=[[0, 1], [1, 2]]
          )
        ]
    else:
        slug_tag = clean.upper().replace(" ", "")[:14]
        beats = [
          dict(
            id="hook",
            type="kinetic_title",
            title=clean.upper()[:32],
            spoken_text=f"Interview mein {clean} pucha jaye toh standard ratta answer mat dena! Aaj iska real production architecture samajhte hain.",
            visual_action="Cinematic reveal of the requested topic.",
            accent_words=[clean, "production architecture"],
            metric=f"{clean.upper()[:18]} ARCHITECTURE",
            nodes=[], connections=[], steps=[]
          ),
          dict(
            id="problem",
            type="comparison",
            title="NAIVE vs PRODUCTION",
            spoken_text=f"Bina {clean} ke high traffic par system bottleneck ho jata hai aur latency spike karti hai. Dekho dono mein farak!",
            visual_action="Compare naive bottleneck against optimized architecture.",
            accent_words=["bottleneck", "latency spike"],
            nodes=[{"label": f"Without {clean[:18]}", "detail": "High latency & bottleneck"}, {"label": f"With {clean[:18]}", "detail": "Scalable & fault-tolerant"}],
            connections=[], steps=[]
          ),
          dict(
            id="architecture",
            type="architecture_build",
            title=f"{clean.upper()[:20]} CORE ENGINE",
            spoken_text=f"{clean} teen core layers mein kaam karta hai: Request Ingestion, Core Processing Engine, aur Fast State Layer.",
            visual_action="Build the core architecture components step by step.",
            accent_words=[clean, "Core Processing"],
            metric="LOW LATENCY",
            nodes=[
              {"label": "Ingestion Layer", "detail": f"Incoming {clean[:15]} requests", "color": "#FF9F2A"},
              {"label": f"{clean[:22]} Engine", "detail": "Core orchestration & routing", "color": "#58A6FF"},
              {"label": "State & Storage", "detail": "Fast in-memory / persistent store", "color": "#3FB950"}
            ],
            connections=[[0, 1], [1, 2]],
            steps=[]
          ),
          dict(
            id="flow",
            type="data_flow",
            title="STEP-BY-STEP FLOW",
            spoken_text=f"Data flow dekho: Request aati hai, {clean} engine usko validate aur process karta hai, aur milliseconds mein response deta hai!",
            visual_action="Animate the topic-specific process from input to output.",
            accent_words=["validate", "milliseconds"],
            metric="< 5MS LATENCY",
            steps=[
              {"label": "1. Request Arrives", "detail": f"Client hits {clean[:18]} layer"},
              {"label": "2. Core Execution", "detail": "Fast lookup & policy check"},
              {"label": "3. Fast Response", "detail": "Guaranteed high-throughput output"}
            ],
            nodes=[], connections=[]
          ),
          dict(
            id="tradeoffs",
            type="comparison",
            title="REAL TRADE-OFFS",
            spoken_text=f"Interview tip: {clean} se speed aur scale toh milti hai, par extra memory aur consistency tradeoff bhi handle karna padta hai!",
            visual_action="Compare benefits and limitations.",
            accent_words=["speed aur scale", "tradeoff"],
            nodes=[{"label": "High Throughput", "detail": "10x faster scale & resilience"}, {"label": "Trade-off", "detail": "Operational & state complexity"}],
            connections=[], steps=[]
          ),
          dict(
            id="summary",
            type="summary",
            title="INTERVIEW TAKEAWAY",
            spoken_text=f"Yaad rakho: {clean} ko problem, data flow aur tradeoffs ke saath explain karo! Comment {slug_tag} for complete PDF interview notes!",
            visual_action="Reveal concise topic takeaway with CTA.",
            accent_words=[clean, slug_tag],
            nodes=[{"label": "Problem", "detail": "Eliminate bottleneck"}, {"label": clean[:20], "detail": "Core processing engine"}, {"label": "Trade-off", "detail": "Scale vs complexity"}],
            connections=[[0, 1], [1, 2]]
          )
        ]
    return {"title": f"{clean}: explained", "topic": clean, "topic_family": profile.family,
            "teaching_format": profile.format_name, "language":"hinglish",
            "target_duration_seconds":duration_seconds,"beats":beats}
