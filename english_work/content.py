"""Job Getting Course (ICT-31, 2026–2027): every homework answer as data — single source for make_english.py.

Facts about the student come only from Англійська/Resume.pdf and the user's answers (English level B1).
Video answers come from the videos' own subtitles (yt-dlp, 30.10.2026); article answers from the article pages;
online-exercise answers from the exercise pages' answer keys. Items that only the student can do (quiz, form,
recording, Telegram) are marked "todo" instead of being invented.

Block markup used by make_english.py:
  ("h2", text)                 task heading inside a lesson
  ("task", text)               the teacher's task, quoted
  ("p", text)                  paragraph; **bold** and *italic* inline
  ("bullets", [..]) / ("num", [..])
  ("table", [header], [[row], ..], [widths in cm])
  ("todo", text)               something the student must do personally
  ("note", text)               short remark / reference to another part
  ("blank", n)                 n empty answer lines to fill in class
"""

STUDENT = "Petro Kravchenko"
GROUP = "ICT-31"
ACCESSED = "30 October 2026"

EMAIL = "petros5325@gmail.com"
PHONE = "+380 99 222 7348"
LINKEDIN = "linkedin.com/in/petro-kravchenko-79b334334"
CITY = "Kyiv, Ukraine"

# ───────────────────────────── vacancies (verified on djinni.co, 30.10.2026) ─────────────────────────────
VACANCIES = [
    dict(company="Rangein", role="Junior DevOps Engineer", posted="20 Oct", fmt="Remote, full-time",
         eng="B2", exp="1–2 years",
         url="https://djinni.co/jobs/854332-junior-devops-engineer/",
         req="Linux and command line; hands-on Docker; CI/CD (GitHub Actions, GitLab CI, Jenkins); one cloud "
             "(AWS, Azure or GCP); Git; Bash or Python scripting; networking, DNS, HTTP/HTTPS; basic IaC; "
             "monitoring and logging",
         plus="Kubernetes, Terraform or Ansible, Prometheus and Grafana, Nginx, Helm or Argo CD"),
    dict(company="RedCore", role="Junior DevOps Engineer", posted="23 Oct", fmt="Remote, full-time",
         eng="B1", exp="2+ years",
         url="https://djinni.co/jobs/854897-junior-devops-engineer/",
         req="2+ years of Linux administration; TCP/IP, HTTP/HTTPS, DNS; Nginx proxying; Prometheus and "
             "Grafana; MongoDB, PostgreSQL, ClickHouse; CI/CD principles; Terraform and Ansible; Git; AWS or "
             "GCP; Kubernetes (EKS), Docker, Bash or Python",
         plus="Cloudflare or another CDN, NATS, Redis, Jira"),
    dict(company="Kyivstar.Tech", role="Network Operations Engineer", posted="16 Oct",
         fmt="Hybrid (Kyiv), full-time", eng="B1", exp="2 years",
         url="https://djinni.co/jobs/853648-network-engineer/",
         req="TCP/IP and OSI; hands-on Cisco switches, routers and wireless; VLANs/802.1Q, STP/RSTP, "
             "EtherChannel; IPv4 subnetting, static routing, OSPF, BGP; Wi-Fi controllers; troubleshooting "
             "with ping, traceroute, SSH, packet captures",
         plus="Cisco Catalyst/Nexus, VXLAN/EVPN, Zabbix or Grafana, ACL/NAT/firewalls, Python or Ansible, CCNA"),
]

# Keywords for the ATS self-check of the new résumé against the Rangein vacancy (the closest match).
ATS_KEYWORDS = ["Linux", "Docker", "CI/CD", "Git", "Bash", "Python", "Nginx", "DNS", "HTTP", "networking",
                "monitoring", "Prometheus", "Grafana", "Kubernetes", "Terraform", "AWS", "Azure", "GCP",
                "Ansible", "GitHub Actions"]

# ─────────────────────────────────────────────── résumé ───────────────────────────────────────────────
RESUME = dict(
    name="PETRO KRAVCHENKO",
    title="Junior DevOps & Network Engineer",
    contacts=[CITY, EMAIL, PHONE, LINKEDIN],
    profile=(
        "Junior DevOps & Network Engineer and third-year Information Systems and Technologies student with a "
        "security-first mindset. Hands-on experience in designing a 3-tier campus network for 700+ users, "
        "containerising and deploying a production website for a German client, and commercial security "
        "auditing (ISO 27001, VAPT). Proficient in Docker, Linux, Nginx, Cisco IOS, Python and SQL; "
        "Cisco Networking Academy certified (CCNA track). Eager to bring end-to-end ownership and a "
        "roll-up-your-sleeves attitude to a DevOps or network team."),
    experience=[
        dict(head="Full-Stack Development & Deployment", org="Luxora (Germany), part-time",
             dates="2026 – present", bullets=[
                 "Develop a business website for a German client: Next.js, HTML/CSS and JavaScript frontend, "
                 "Python backend and a Supabase (PostgreSQL) database with migrations.",
                 "Containerise the application with Docker and run it on a Linux VPS "
                 "behind an Nginx reverse proxy.",
                 "Provide ongoing support, updates and performance monitoring of the production environment."]),
        dict(head="Campus Network Design & Deployment", org="KNU / personal project", dates="2026", bullets=[
            "Designed and built a 3-tier hierarchical network (core / distribution / access) from scratch "
            "for 700+ users.",
            "Implemented VLANs, inter-VLAN routing, STP and redundant uplinks so that the network stays "
            "available when a single link fails.",
            "Secured the network with port security, DHCP snooping, DAI, ACLs and WPA3 wireless.",
            "Produced full physical and logical documentation and an IP addressing plan; monitored "
            "performance after deployment."]),
        dict(head="Efficiency Unit Lead", org="KNU Faculty Student Parliament", dates="2025 – present", bullets=[
            "Build KPI frameworks, analytical dashboards and reporting systems to track the performance "
            "of cross-department work."]),
        dict(head="Cybersecurity Audit & Penetration Testing", org="Business Continuity Solutions LLC",
             dates="2025", bullets=[
                 "Performed an ISO 27001-based security audit and a full internal and external VAPT for a "
                 "commercial client.",
                 "Analysed WPA2/WPA3 wireless vulnerabilities and delivered a prioritised remediation report."]),
    ],
    skills=[
        ("Networking", "Cisco IOS, routing & switching (L2/L3), VLANs, STP, ACLs, VPN, TCP/IP, "
                       "3-tier network design"),
        ("DevOps", "Docker, Docker Compose, Linux administration & hardening, Nginx, Git, Bash, Grafana, "
                   "Prometheus, Kubernetes (K8s), Akamai/Linode, Vercel"),
        ("Security", "Penetration testing (VAPT), ISO 27001, WPA2/WPA3 analysis, Kali Linux, risk assessment"),
        ("Development", "Python, SQL, PostgreSQL, Supabase, JavaScript, Next.js, React, HTML/CSS, C++, Java"),
        ("Currently learning", "Terraform, AWS / Azure, CI/CD pipelines"),
    ],
    education=[("B.Sc. in Information Systems and Technologies (programme: IoT Software Technologies)", "Taras Shevchenko National University of Kyiv · 2024 – present "
                "(expected graduation: 2028) · GPA 90+/100")],
    certs=[
        "Cisco Networking Academy: CCNA: Introduction to Networks; CCNA: Switching, Routing, and Wireless "
        "Essentials; CCNA: Enterprise Networking, Security, and Automation; Cybersecurity Essentials",
        "Google.org & Hackathon 2025: Fundamentals of Cybersecurity for Small Organizations",
        "Oracle: Database Foundations",
        "In progress: Mate Academy DevOps track",
    ],
    languages=[("Ukrainian", "native"), ("English", "B1 (Intermediate)")],
)

RESUME_CHANGES = [
    ("Job title", "«DevOps Engineer & Network» (grammatically incomplete)",
     "«Junior DevOps & Network Engineer»"),
    ("Languages", "missing", "added: Ukrainian (native), English B1 — a required section"),
    ("Font", "Evolventa (decorative)", "Arial, 10–11 pt body, 14 pt headings (teacher's “Fonts matter” rules)"),
    ("Images", "Cisco, Oracle and Docker logos", "logos removed (ATS cannot read images); the photo stays"),
    ("Layout", "two text columns", "one column with standard headings — easier for an ATS to read"),
    ("Verb tenses", "«Developing…», «Handling…» for current work",
     "base form for current roles (Develop, Build), past tense for finished ones (Designed, Performed)"),
    ("Profile", "7 lines; «Certified across 5 Cisco courses» while only 4 Cisco courses are listed",
     "4 sentences (who I am, what I offer, what I bring); no unverifiable count"),
    ("Education", "«2024–present | GPA 90+»", "full degree name, expected graduation 2028, GPA 90+/100"),
    ("Contacts", "LinkedIn only as a hidden hyperlink", "full LinkedIn URL in text, readable by people and ATS"),
]

# ───────────────────────────────────────────── cover letter ─────────────────────────────────────────────
COVER = dict(
    date="30 October 2026",
    to=["Hiring Team", "Rangein"],
    re="Junior DevOps Engineer (Djinni, published on 20 October 2026)",
    greeting="Dear Hiring Manager,",
    paras=[
        "After learning about the Junior DevOps Engineer position at Rangein, I became interested in it because "
        "it combines the things I enjoy most: Docker, Linux, automation and keeping services healthy in "
        "production. I am a third-year Information Systems and Technologies student at Taras Shevchenko National "
        "University of Kyiv, and I would like to apply for this role.",
        "Your job description mentions hands-on Docker experience, Linux, Nginx, networking fundamentals and "
        "monitoring. These are exactly the areas I work in every week. For Luxora, a company from Germany, I "
        "develop a business website and I am responsible for its deployment: I containerised the application "
        "with Docker, deployed it to a Linux VPS behind an Nginx reverse proxy, and now I "
        "support and monitor the production environment. This project taught me to take end-to-end ownership "
        "of a service.",
        "I understand that my commercial experience is shorter than one to two years. However, my background in "
        "networking and security makes up for part of it. I designed a three-tier campus network for more than "
        "700 users, with VLANs, redundant uplinks and security features such as DHCP snooping and ACLs, and I "
        "carried out an ISO 27001-based audit and a penetration test for a commercial client. I am also "
        "completing the Mate Academy DevOps track to strengthen my CI/CD, Terraform and cloud skills.",
        "I would welcome the opportunity to discuss how I can contribute to your team. My résumé is attached, "
        f"and you can contact me at {EMAIL} or {PHONE}. Thank you for your time and consideration.",
    ],
    closing="Sincerely,",
)

# ─────────────────────────────────────────────── pitch ───────────────────────────────────────────────
PITCH = [
    ("1. Self-introduction",
     "Hello! My name is Petro Kravchenko. I'm a junior DevOps and network engineer with a passion for "
     "reliable and secure infrastructure, and a third-year student of Information Systems and Technologies at "
     "Taras Shevchenko National University of Kyiv."),
    ("2. Key skills",
     "I'm proficient in Docker, Linux and Nginx, and I'm experienced in Cisco networking — VLANs, routing and "
     "network security. I'm also familiar with Python, SQL and monitoring with Grafana and Prometheus."),
    ("3. Achievements",
     "I designed a three-tier campus network for more than 700 users. Now I develop and deploy a business "
     "website for Luxora, a company from Germany: I containerised it with Docker and run it on a Linux server "
     "behind Nginx. I have also carried out an ISO 27001-based security audit and a penetration test for a "
     "commercial client."),
    ("4. Problems I can solve",
     "I specialise in building and supporting infrastructure that is fast, secure and easy to maintain — "
     "from the network to the container."),
    ("5. Call to action",
     "I look forward to demonstrating how I can add value to your team. Let's talk!"),
]

# ─────────────────────────────────────────── vocabulary bank ───────────────────────────────────────────
VOCAB = [
    ("16/09", [
        ("to sell yourself short", "to underestimate your skills",
         "Don't sell yourself short: a student project for 700 users is real experience."),
        ("top-notch", "excellent, of the highest quality",
         "Our university has a top-notch Cisco lab."),
        ("to nail a job interview", "to succeed in a job interview",
         "I practise my pitch every day because I want to nail my next job interview."),
        ("to nourish", "to feed, to support the growth of",
         "Good feedback nourishes a young specialist's motivation."),
        ("a joint project", "a project done together",
         "The campus network was a joint project of our study group."),
        ("a hackathon", "a short event where teams build a product",
         "I received a cybersecurity certificate through a Google.org hackathon in 2025."),
        ("to increase", "to become or make bigger",
         "Caching can increase the speed of a website."),
        ("to feel in one's element", "to feel comfortable and confident",
         "I feel in my element when I configure a Linux server."),
        ("to stand out from the crowd", "to be noticeably different or better",
         "Real projects help a junior engineer stand out from the crowd."),
        ("to think on one's feet", "to react quickly in an unexpected situation",
         "When the website went down, I had to think on my feet."),
    ]),
    ("23/09", [
        ("underlying strengths", "basic strengths behind your skills",
         "My underlying strengths are logic and attention to detail."),
        ("a skills toolkit", "a set of skills",
         "Docker and Git are an important part of my skills toolkit."),
        ("to have a knack for", "to have a natural ability",
         "I have a knack for finding the cause of network problems."),
        ("a seasoned specialist", "an experienced professional",
         "I would like to learn from seasoned specialists in a DevOps team."),
    ]),
    ("26/09", [
        ("concise", "brief, short and clear", "A résumé should be concise — one page is enough for a student."),
        ("to thrive", "to grow and be successful", "I thrive in teams where people share knowledge."),
        ("a hands-on role", "a job with direct practical work",
         "I am looking for a hands-on role where I can work with real servers."),
        ("to wear multiple hats", "to have several roles at the same time",
         "At Luxora I wear multiple hats: developer, DevOps engineer and support."),
        ("vague", "not clear or specific", "“Helped with IT tasks” is too vague for a résumé."),
    ]),
    ("30/09", [
        ("teething problems", "temporary problems at the start of something new",
         "The new deployment had some teething problems, but we fixed them in a day."),
        ("business acumen", "good understanding of business",
         "Business acumen helps an engineer understand why uptime matters to the client."),
        ("to take initiative", "to act without being told",
         "I took initiative and wrote documentation for the whole network."),
        ("to leverage keywords", "to use keywords to get the best result",
         "I leverage keywords from the job description, such as Docker and CI/CD."),
    ]),
    ("07/10", [
        ("in a nutshell", "briefly",
         "In a nutshell, I build and support infrastructure that is fast and secure."),
    ]),
    ("21/10", [
        ("seasoned", "experienced", "She is a seasoned network engineer with ten years in telecom."),
        ("to leverage keywords", "to use them to achieve a maximum result",
         "An ATS ranks higher the résumés that leverage the right keywords."),
        ("to forge positive relationships", "to build strong, friendly relationships",
         "Regular updates help me forge positive relationships with clients."),
        ("a sleek app", "a modern, stylish and simple application",
         "The client wanted a sleek app that loads fast on mobile phones."),
        ("adept at something", "very skilled at something", "I am adept at troubleshooting Linux servers."),
    ]),
    ("28/10", [
        ("to get the ball rolling", "to start an activity or process",
         "To get the ball rolling, I updated my LinkedIn headline."),
        ("relentless", "continuing without stopping",
         "Technology changes at a relentless pace, so engineers never stop learning."),
        ("novelty", "the quality of being new",
         "The novelty of remote work wears off, but the flexibility stays."),
        ("come rain or shine", "whatever happens",
         "Come rain or shine, the production website must stay online."),
        ("to endorse", "to publicly support or recommend",
         "My teammates endorsed my Docker and Linux skills on LinkedIn."),
        ("a roll-up-your-sleeves attitude", "willingness to work hard",
         "Employers value a roll-up-your-sleeves attitude in junior engineers."),
        ("tremendous", "very good; very great", "Mentoring can make a tremendous difference to a junior."),
        ("eager to learn", "wanting to learn",
         "I am eager to learn Terraform and cloud services."),
    ]),
]

PRONUNCIATION = [
    ("faculty", "/ˈfæk.əl.ti/"), ("Python", "/ˈpaɪ.θən/"), ("parliament", "/ˈpɑː.lə.mənt/"),
    ("architecture", "/ˈɑː.kɪ.tek.tʃə/"), ("event", "/ɪˈvent/"), ("accomplishment", "/əˈkʌm.plɪʃ.mənt/"),
    ("initiative", "/ɪˈnɪʃ.ə.tɪv/"), ("accuracy", "/ˈæk.jə.rə.si/"),
    ("organised", "/ˈɔː.ɡən.aɪzd/ (BrE), /ˈɔːr.ɡən.aɪzd/ (AmE)"), ("creative", "/kriˈeɪ.tɪv/"),
    ("successful", "/səkˈses.fəl/"),
]

# ─────────────────────────────────────────────── lessons ───────────────────────────────────────────────
V = {v["company"]: v for v in VACANCIES}

LESSONS = [
    ("09/09/2026", "Job Search Basics for Young Professionals", [
        ("h2", "1. Video: “Job & Career Advice for Young People” (WGN News) — career tips"),
        ("task", "Watch the video and get career tips for young people."),
        ("p", "In the video, New York Times reporter Emma Goldberg, who writes about work and careers, gives "
              "three main tips:"),
        ("num", [
            "**Think about a dream career, not one dream job.** Jobs change very quickly because of artificial "
            "intelligence and automation, so it is healthier to find your underlying passion and skills — for "
            "example storytelling, engineering or data analytics — which open many different jobs.",
            "**Use the “seven stories” method.** Remember about seven moments in your life when you felt that "
            "your personal gifts were recognised, and connect them to possible jobs and careers.",
            "**Breadth, not only depth.** Experts talk about *exploration* versus *exploitation*: going deep "
            "into one thing is useful, but young people benefit even more from trying many activities, even "
            "outside their comfort zone, because they may discover unexpected interests and skills.",
        ]),
        ("p", "**My takeaway.** My own “stories” are the moments when I built something that other people "
              "use: the campus network for 700+ users and the website that I deploy for Luxora. They point "
              "to one career — building and supporting infrastructure — rather than to a single job title."),
        ("h2", "2. BBC article: “Six essential skills employers say job seekers should have to stand out”"),
        ("task", "Read and be ready to discuss."),
        ("p", "The article (BBC, education editor Branwen Jeffreys) reports a five-year study by the National "
              "Foundation for Educational Research (NFER). It names six transferable skills that will count as "
              "much as qualifications. My discussion notes:"),
        ("table", ["Skill", "What employers in the article say", "My example"], [
            ["Organising, planning and prioritising",
             "Christian Townsley (North Bar): keep a “cool head”, organise and multitask.",
             "I combine full-time study with part-time work for Luxora and my role in the Student Parliament."],
            ["Problem solving and decision-making",
             "Maria Aderonmu learnt to think on her feet; India Chaplin: use problem-solving experience from "
             "outside work.",
             "Choosing redundant uplinks and STP for the campus network so that one failed link does not stop "
             "the network."],
            ["Communication",
             "Jake Readman: develop communication skills and learn to de-escalate conflict.",
             "Explaining technical decisions and giving updates to the client at Luxora."],
            ["Collaboration",
             "Lynn Bassett (Barbour): every department is interlinked, so working as one team is important.",
             "KPI dashboards and reports for cross-department work in the Student Parliament."],
            ["Creative thinking",
             "Barbour asks: “Give us an example of when something's not gone to plan and how you got it back "
             "on track.”",
             "Finding a way to fit security features (port security, DHCP snooping, DAI) into one network "
             "design."],
            ["Information literacy (evaluating data)",
             "India Chaplin: raw data does not “tell a story” — you must understand what it tells us.",
             "Reading monitoring data from Grafana and Prometheus; building analytical dashboards."],
        ], [3.6, 6.4, 6.0]),
        ("p", "**For discussion.** The article says that 42% of employers named a lack of soft skills or work "
              "readiness as a challenge when they hire young people. In my opinion, for IT the most important "
              "skill from the list is problem solving, because a DevOps engineer's day is mostly about finding "
              "the cause of a problem and fixing it. However, without communication even a good solution can "
              "fail, because the team and the client must understand it."),
        ("h2", "3. Vocabulary exercises “Work”"),
        ("p", "**Task 1. Verbs** — match the words in bold with their definitions."),
        ("table", ["#", "Definition", "Answer"], [
            ["1", "to give up a job", "to resign"],
            ["2", "to ask for a job, usually by writing a letter", "to apply for"],
            ["3", "to be removed from a job because you have done something bad", "to be dismissed"],
            ["4", "same as 1", "to hand in your notice"],
            ["5", "to stop work and take a pension", "to retire"],
            ["6", "to write in the empty spaces on a form", "to fill in"],
            ["7", "to be given a better job in the organisation", "to be promoted"],
            ["8", "to be questioned by people when you apply for a job", "to attend an interview"],
            ["9", "to travel to work from home each day", "to commute"],
            ["10", "to be dismissed for a time until more work is available", "to be laid off (lay off)"],
        ], [1.0, 10.0, 5.0]),
        ("p", "**Task 2. Nouns** — fill in the gaps."),
        ("p", "A computer company had a (1) **vacancy** for the position of (2) **salesman**, and decided to "
              "advertise for a new (3) **employee**. A lot of (4) **applicants** with good (5) "
              "**qualifications** and (6) **references** applied for the job, and after all the interviews had "
              "finished, the directors made a (7) **shortlist** of the best (8) **candidates**, then invited "
              "them to come back for another interview."),
        ("p", "The person who eventually got the job was very happy. After all, he would receive an annual (9) "
              "**salary** of £25,000, with a 5% (10) **increment** twice a year, a 15% (11) **commission** for "
              "each computer he managed to sell, excellent (12) **perks** such as private health insurance and "
              "a company car, a company (13) **pension** to make sure he would be well-off when he retired, and "
              "the chance of (14) **promotion** from salesman to sales (15) **manager** if he was successful. "
              "All in all, his future (16) **prospects** looked very good."),
        ("note", "Gaps 4 and 8 can swap: applicants / candidates."),
    ]),

    ("16/09/2026", "Job hunting", [
        ("h2", "1. Vocabulary"),
        ("note", "Learnt — see my example sentences in Appendix A (16/09)."),
        ("h2", "2. Quiz “What is your tech personality?” (Codecademy)"),
        ("todo", "Take the quiz at codecademy.com/explore/sorting-quiz and add a screenshot of your result here. "
                 "The result depends on your own answers, so it cannot be prepared in advance."),
        ("h2", "3. Video: “Tell Me About Yourself — an excellent answer” (English with Lucy) — my takeaways"),
        ("bullets", [
            "Talk about **work, not your personal life**. Keep your life stories for later.",
            "Give a **brief overview** — like the text on the back of a book: interesting, but not the whole story.",
            "If your experience is similar to the job, start at the beginning; if not, **start with the most "
            "relevant position**.",
            "A new graduate can talk about **university, part-time jobs and volunteering**, not only paid work.",
            "For each experience, mention **one major achievement** — hard (a new programming language) or soft "
            "(communication, solving a problem) — and be specific.",
            "Finish by connecting your skills to **the job you are applying for**; research the company first.",
        ]),
        ("p", "**My answer to “Tell me about yourself” (Lucy's homework task):**"),
        ("p", "*“I'm a third-year Information Systems and Technologies student at Taras Shevchenko National "
              "University of Kyiv, and I'm starting my career in DevOps and networking. My first big project was "
              "a three-tier campus network for more than 700 users: I designed the VLANs, routing and security, "
              "and documented everything. Now I work part-time for Luxora, a company from Germany: I develop "
              "their website and I'm responsible for its deployment with Docker and Nginx on a Linux server. "
              "One of my proudest moments was delivering an ISO 27001-based security audit to a commercial "
              "client. I understand from your job post that you need someone who can support Linux and Docker "
              "infrastructure, and I'm sure that my practical experience will help me do that well.”*"),
        ("h2", "4. My 3–4 hard and 4 soft skills"),
        ("table", ["Hard skills", "Soft skills"], [
            ["Cisco networking: VLANs, inter-VLAN routing, STP, ACLs",
             "Accountable by default — I support the Luxora website in production"],
            ["Docker, Docker Compose, Linux administration, Nginx",
             "Systems-minded — I designed a network with core, distribution and access layers"],
            ["Python and SQL (PostgreSQL, Supabase)",
             "Collaborative — I build reports for cross-department work in the Student Parliament"],
            ["Security auditing: ISO 27001, penetration testing (VAPT)",
             "Learning-agile — Cisco courses, Oracle and Mate Academy while studying full-time"],
        ], [8.0, 8.0]),
    ]),

    ("23/09/2026", "Elevator pitch. Transferable skills", [
        ("h2", "1. The type of job I'm interested in"),
        ("table", ["Item", "My answer"], [
            ["Role", "Junior DevOps Engineer (second option: Junior Network Engineer)"],
            ["Tasks", "maintain CI/CD pipelines; build and run Docker containers; administer Linux servers and "
                      "Nginx; monitor services (Prometheus, Grafana) and investigate alerts; automate routine "
                      "work with Bash or Python; document the infrastructure"],
            ["Type", "a technical infrastructure and operations role in an IT product or service company"],
            ["Market", "international (remote) and local (Kyiv)"],
            ["Format", "part-time while I study; full-time after graduation"],
        ], [3.0, 13.0]),
        ("h2", "2. Relevant vacancies and their requirements"),
        ("p", f"Three real vacancies from Djinni, published in October 2026 (checked on {ACCESSED}):"),
        ("table", ["Company and role", "Format, English, experience", "Key requirements", "Nice to have"],
         [[f"**{v['company']}** — {v['role']} ({v['posted']})", f"{v['fmt']}; English {v['eng']}; {v['exp']}",
           v["req"], v["plus"]] for v in VACANCIES], [3.2, 3.4, 6.2, 3.2]),
        ("p", "**What the vacancies have in common:** Linux, Docker, Git, CI/CD, Bash or Python scripting, "
              "networking fundamentals (TCP/IP, DNS, HTTP) and monitoring. English B1–B2 is enough."),
        ("p", "**My match.** I already have Linux, Docker, Nginx, Git, Python, networking, Cisco and basic "
              "monitoring. My gaps are commercial experience (the vacancies ask for 1–2 years), CI/CD pipelines, "
              "Terraform or Ansible, and a cloud platform (AWS, Azure or GCP). My plan is to finish the Mate "
              "Academy DevOps track and add a CI/CD pipeline to my Luxora project."),
        ("h2", "3. My pitch"),
        ("note", "Structure: self-introduction → key skills → achievements → problems I can solve → call to "
                 "action. The same text is in the file “Pitch_script_Petro_Kravchenko”, ready for the video."),
        ("pitch", None),
    ]),

    ("26/09/2026", "Interesting facts about résumé writing. Résumé structure", [
        ("h2", "1. Video: “CV vs Resume: What's the difference?” (Resume Genius)"),
        ("bullets", [
            "Most of the time the two words mean the same thing: a document that shows your work experience, "
            "education and skills.",
            "In the **USA and Canada**, a *résumé* is a one- or two-page document for a job search; it focuses on "
            "your most relevant experience. A *CV* there usually means an **academic CV**: publications, "
            "conferences, teaching, dissertations — for grad school, research or medicine.",
            "In the **UK and most of Europe**, *CV* is used both for jobs and for academia; the word *résumé* "
            "is less common but understood.",
            "**For me:** for Ukrainian and European companies I can say “CV”; for an American company — "
            "“résumé”. The content is the same one-page document.",
        ]),
        ("h2", "2. Article: “Interesting Facts About Resume Writing” (Timothy Lewis, LinkedIn)"),
        ("p", "Key facts from the article:"),
        ("num", [
            "Recruiters spend only **6–7 seconds** on a résumé, so the name, contacts, job title and key skills "
            "must be easy to find.",
            "Up to **75%** of résumés are filtered out by an Applicant Tracking System (ATS) before a person "
            "sees them.",
            "**Bullet points** make a résumé easier to read.",
            "A **tailored** résumé increases your chances of getting noticed by 50%.",
            "**Numbers** speak louder than words: “Increased sales by 20% in 6 months”.",
            "One page is ideal for most people with less than 10 years of experience.",
            "**Irrelevant information** is a common mistake.",
            "**Keywords** from the job posting matter, but do not “keyword stuff”.",
            "**White space** is not wasted space.",
            "**Education does not always come first** — unless you are a recent graduate or apply for an "
            "academic role.",
        ]),
        ("p", "**For discussion.** The most surprising fact for me is the 6–7 seconds. That is why I put my job "
              "title and the main keywords (Docker, Linux, Cisco) at the very top of my résumé. I do not fully "
              "agree with fact 10 for students: Google's recruiters (video of 30/09) say that students should "
              "put education first. As a student, I keep education near the top but after my projects, because "
              "my projects show more of what I can do."),
        ("h2", "3. Vacancies and requirements"),
        ("note", "See the vacancy analysis in the lesson of 23/09 (three vacancies from October 2026)."),
        ("h2", "4. Résumé template and summary"),
        ("p", "My résumé has all the required sections: photo; contact information (name, phone, email, "
              "LinkedIn, city and country); summary; experience and projects; skills; education and "
              "certifications; languages. The final version is in the file “Resume_Petro_Kravchenko”."),
        ("table", ["Question", "My summary"], [
            ["Who are you?", "A junior DevOps & network engineer and a third-year Information Systems and "
                             "Technologies student with a security-first mindset."],
            ["What can you offer?", "Docker, Linux, Nginx, Cisco networking, Python and SQL; a 3-tier network "
                                    "for 700+ users; a production website deployed for a German client; an "
                                    "ISO 27001-based audit."],
            ["What value can you bring?", "End-to-end ownership of infrastructure: I build it, secure it and "
                                          "keep it running, so the team can focus on the product."],
        ], [4.0, 12.0]),
        ("h2", "5. Video 3.1.1: Esther, a jobseeker applying for an internship"),
        ("note", "The coursebook video (with James Caan and careers coach John Lees) is not available online, "
                 "so the answers that need the video are left as lines to complete in class. Questions that "
                 "do not depend on the video are answered."),
        ("p", "**Ex. 2.** Three rules for writing a CV:"),
        ("blank", 3),
        ("p", "**Ex. 3.** 1, 2, 4, 5, 6 — complete after watching:"),
        ("blank", 5),
        ("p", "**Ex. 3, question 3.** *Soft skills* are personal qualities: communication, teamwork, time "
              "management, problem solving, adaptability. *Hard skills* are technical abilities that you can "
              "learn and measure: configuring Cisco routers, writing Python, using Docker, speaking a foreign "
              "language."),
        ("p", "**Ex. 3, question 7.** “Getting a job is a job in itself” means that looking for a job takes as "
              "much time and effort as real work: you research companies, tailor your CV for every vacancy, "
              "write cover letters and prepare for interviews."),
        ("p", "**Ex. 4.** Rule 3, gaps 1–6 — complete after watching:"),
        ("blank", 2),
        ("p", "**Ex. 5.1.** To stand out from the crowd at an interview, I would give one concrete example "
              "instead of general words: “I designed a network for 700+ users” sounds stronger than “I'm a "
              "hard-working team player”. I would also show that I know the company and ask a good question "
              "at the end."),
        ("p", "**Ex. 5.2.** Positive characteristics: responsible, calm under pressure, curious. Skills: "
              "network design (Cisco), Docker and Linux, Python."),
    ]),

    ("30/09/2026", "Tips for creating a killer résumé", [
        ("h2", "1. Video: “Create Your Resume for Google: Tips and Advice” — my insights"),
        ("bullets", [
            "Simple and consistent format; **PDF** is preferred; contacts at the top; no references needed.",
            "**One page** for business and internship roles, no longer than **two pages** for engineering roles.",
            "For technical candidates: list **programming languages** at the top and add a **GitHub** profile.",
            "Students and recent graduates put **education first**, with the (expected) graduation date in "
            "*month year* format and the GPA.",
            "Experience is not only jobs: research, tutoring, personal and class projects, hackathons.",
            "Use **action words** (created, designed, debugged…) and the words of the job description.",
            "The Google formula: **“Accomplished [X] as measured by [Y], by doing [Z]”**.",
            "The most important tip: **always check for typos**.",
        ]),
        ("p", "**What I changed after the video:** I added the expected graduation year and the GPA, kept "
              "programming languages in the Skills section and used action verbs. Next step: create a public "
              "GitHub profile with my network and Docker projects and add the link to my résumé."),
        ("h2", "2. Text “6 Tips for Creating a Killer Resume” — exercises"),
        ("p", "**Exercise 1B.** Find the highlighted terms:"),
        ("table", ["#", "Meaning", "Term"], [
            ["1", "Immediately", "right out of the gate"],
            ["2", "Reviewing written work and marking any errors", "proofreading"],
            ["3", "Including all aspects of something", "comprehensive"],
            ["4", "Submit a request", "apply (for)"],
            ["5", "Adapted for a particular purpose", "tailored (for)"],
            ["6", "People looking for a job", "job seekers"],
            ["7", "Remove or delete", "take off"],
            ["8", "The “empty” area of a page", "white space"],
            ["9", "Someone who can give you a job", "prospective employer"],
            ["10", "Be noticeable due to uniqueness", "stand out"],
            ["11", "Improve or increase", "boost"],
            ["12", "Highlight or draw attention to", "showcase"],
        ], [1.0, 9.0, 6.0]),
        ("p", "**Exercise 1C.** Antonyms: 1 showcase — **b** (hide); 2 extensive — **a** (small, limited); "
              "3 boost — **d** (hinder, decrease); 4 take off — **c** (add)."),
        ("p", "**Exercise 1D.**"),
        ("num", [
            "Should I **take off** my contact details? I don't think I need to include them.",
            "We have conducted **extensive** research on this topic.",
            "I **boosted** sales by over 50% within two months.",
            "If you want to **showcase** your work, you will need a portfolio.",
        ]),
        ("p", "**Exercise 2.** About my résumé:"),
        ("num", [
            "I created the first version in Canva in June 2026 and updated it in October 2026 after the "
            "analysis in class.",
            "The first version was a Canva template with my own design: two columns, a round photo and "
            "company logos. The final version is a simpler one-column layout, which is easier for an ATS.",
            "Yes. I kept it relevant to DevOps and networking, did not include personal details (age, marital "
            "status, hobbies), focused on achievements with numbers (700+ users), kept it to one page, used keywords "
            "from vacancies (Docker, Linux, CI/CD) and proofread it.",
        ]),
    ]),

    ("07/10/2026", "Achievements. Education", [
        ("h2", "1. Task 1.2 — complete the résumé summaries"),
        ("num", [
            "Computer science student, passionate about Operating Systems. **Knowledgeable** about Linux kernel "
            "development.",
            "**Seasoned** PHP programmer with over 7 years of industry experience. **Adept** at creating dynamic "
            "web pages that don't require much upkeep. **Proficient** in Laravel.",
            "Experienced mobile developer skilled at React Native and Flutter. Passionate about creating "
            "**sleek**, efficient applications that solve business problems.",
            "Project Manager with over 5 years of experience in managing complex software projects and an "
            "**extensive** background in QA and business analysis. Focused on **leveraging** teamwork to deliver "
            "optimal business solutions.",
        ]),
        ("h2", "2. Task 1.3 — match the action verbs"),
        ("table", ["#", "Sentence"], [
            ["1", "**Boosted** backtesting speed by 200%"],
            ["2", "**Led** a team of 7 people using Agile methodology to create an e-commerce website"],
            ["3", "**Forged** positive relationships with clients and vendors, increasing the company's annual "
                  "profit margin by 30%"],
            ["4", "**Designed** innovative design solutions to create intuitive web interfaces"],
            ["5", "**Ensured** successful database migrations and data security"],
            ["6", "**Decreased** page load speed by 40% (more precisely: page load *time*)"],
            ["7", "**Optimized** the app's performance by 60% using code refactoring"],
            ["8", "**Advised** the design team on best practices and approaches"],
            ["9", "**Wrote** automation scripts that made the testing process 60% more efficient"],
            ["10", "**Analyzed** customer feedback and market trends to come up with best technical solutions"],
        ], [1.0, 15.0]),
        ("note", "“Performed” is the extra verb in the box."),
        ("h2", "3. My achievements by the formula"),
        ("p", "Formula: **action verb + tool or technology + result + number**."),
        ("table", ["Action verb", "Tool / technology", "Result", "Number"], [
            ["Designed and built", "Cisco: VLANs, inter-VLAN routing, STP, redundant uplinks",
             "a 3-tier campus network that stays available when one link fails", "700+ users"],
            ["Containerise and run", "Docker, Linux VPS, Nginx",
             "the client's website in production", "1 production website (Luxora, Germany)"],
            ["Secured", "port security, DHCP snooping, DAI, ACLs, WPA3", "a protected campus network",
             "5 security features"],
            ["Performed", "ISO 27001, internal and external VAPT", "a prioritised remediation report",
             "1 commercial client"],
            ["Build", "KPI frameworks and analytical dashboards", "performance tracking of cross-department work",
             "—"],
        ], [3.0, 5.0, 5.0, 3.0]),
        ("note", "I did not add numbers that I cannot prove (for example, % of faster deployment). When I "
                 "measure them, I will add them to the bullets."),
        ("h2", "4. Education section"),
        ("p", "**B.Sc. in Information Systems and Technologies** (educational programme: IoT Software "
              "Technologies), Taras Shevchenko National University of Kyiv, 2024 – present (expected graduation: "
              "2028), GPA 90+/100."),
        ("p", "**Certifications:** Cisco Networking Academy — CCNA: Introduction to Networks; CCNA: Switching, "
              "Routing, and Wireless Essentials; CCNA: Enterprise Networking, Security, and Automation; "
              "Cybersecurity Essentials. Google.org & Hackathon 2025 — Fundamentals of Cybersecurity for Small "
              "Organizations. Oracle — Database Foundations. In progress: Mate Academy DevOps track."),
    ]),

    ("14/10/2026", "Analysis of your résumés", [
        ("h2", "1. Video: Warren Buffett and Charlie Munger explain the circle of competence"),
        ("bullets", [
            "Buffett: the key is to know **the perimeter of your circle of competence** — where it begins and "
            "ends.",
            "Even Buffett went outside his circle: most often in retail (a department store in Baltimore) and "
            "when he decided to buy control of Berkshire Hathaway — “a dumb decision”, which worked out.",
            "Mrs B of the Furniture Mart knew exactly **what she knew and what she didn't** — she refused "
            "stock because she did not understand it — and that took her a long way.",
            "To learn where your circle is, ask **friends who know you well** for honest feedback.",
            "Munger: competence is **relative** — play the games where you can win.",
        ]),
        ("table", ["Circle", "Me"], [
            ["What I know and what matters for my job", "Linux, Docker, Nginx, Cisco networking, network "
                                                        "security, Python, SQL"],
            ["What I don't know yet, but it matters", "CI/CD pipelines, Terraform, AWS / Azure, deeper "
                                                      "Kubernetes — this is my learning plan"],
            ["What doesn't matter for my career now", "for example, mobile app design or video editing"],
        ], [6.0, 10.0]),
        ("h2", "2. ATS self-check of the final résumé"),
        ("p", "The teacher's ATS checkers (Jobscan, Resume Worded, Enhancv) need an account and an upload, so "
              "I made the same check myself: I compared the text of my final résumé with the keywords of the "
              "Rangein vacancy (my closest match)."),
        ("ats", None),
        ("todo", "Optional: upload Resume_Petro_Kravchenko.pdf to jobscan.co together with the Rangein job "
                 "description and compare the score."),
        ("h2", "3. Send the résumé to the teacher"),
        ("todo", "Send Resume_Petro_Kravchenko.pdf to the teacher via Telegram."),
    ]),

    ("21/10/2026", "Analysis of your résumés. Webinar “The Power of You”", [
        ("h2", "1. Revise and improve the résumé"),
        ("p", "The final version is in the file “Resume_Petro_Kravchenko” (PDF and DOCX). What I changed:"),
        ("changes", None),
        ("h2", "2. Video: “How to Write a Cover Letter” (Speak Confident English)"),
        ("p", "**1. When do you need a cover letter?** Always when the job description asks for one; never when "
              "it says not to send one. If it says nothing, a cover letter is a good idea when someone referred "
              "you to the position, when something in your résumé needs an explanation (a gap in your work "
              "history or a background that does not match perfectly), or when you are changing your career "
              "field."),
        ("p", "**2. Why might a cover letter be useful to you?** A well-written cover letter helps you stand out "
              "from the competition. You can mention a referral, explain a gap or a career change, and say why "
              "you are the right person for the job."),
        ("p", "**How is it different from a résumé?** A résumé is **objective**: only facts about your education, "
              "experience, responsibilities and achievements, written in bullet points without “I” or “you”. A "
              "cover letter is **subjective**: it explains why you are the right fit and how your skills will "
              "help the company. It is personal and conversational, written in paragraphs, and it tells one or "
              "two stories instead of repeating the résumé."),
        ("p", "**3. The four tips for writing a perfect cover letter:**"),
        ("num", [
            "**Write it like a professional business letter.** Find the name of the person and avoid “To whom it "
            "may concern”; if you cannot find a name, write “Dear Hiring Manager”.",
            "**Make it conversational.** Use “I” and “you”: the résumé line “Led a team of 14…” becomes “I led a "
            "team of 14…” with more detail.",
            "**Include keywords** from the job description and from what you read about the company.",
            "**Use three or four paragraphs**: an introduction (how you found the position and what excites you), "
            "one or two paragraphs about your value with one story, and a closing with a call to action. Keep it "
            "to one page and do not repeat your résumé.",
        ]),
        ("note", "My own cover letter, written with these four tips, is in the file "
                 "“Cover_letter_Petro_Kravchenko” (for the Rangein vacancy)."),
        ("h2", "3. Useful tips: my soft skills and unique qualities"),
        ("p", "Following the teacher's example (*skill: where I show it*) and replacing template words with "
              "stronger ones:"),
        ("table", ["Template word", "Stronger word", "Where I show it"], [
            ["responsible", "accountable by default, end-to-end ownership",
             "I build, deploy and support the Luxora website myself."],
            ["stress-resistant", "composed under pressure",
             "Troubleshooting a production website when it must work come rain or shine."],
            ["attentive to details", "meticulous",
             "Full physical and logical documentation and an IP plan for the campus network."],
            ["communicative", "bridge-building",
             "Explaining technical decisions to the client and reporting to several departments."],
            ["fast learner", "learning-agile",
             "Cisco, Oracle and Mate Academy courses on top of full-time study."],
        ], [3.4, 4.6, 8.0]),
        ("p", "**Unique qualities:** *systems-minded* — I see the whole chain from the network cable to the "
              "Docker container; *security-first* — I think about protection while I design, not after; "
              "*evidence-led* — I trust monitoring data more than guesses."),
    ]),

    ("28/10/2026", "Cover letter. Feedback. The benefits of using LinkedIn", [
        ("h2", "1. Learn new words"),
        ("note", "Learnt — see my example sentences in Appendix A (28/10)."),
        ("h2", "2. Submit the final version of the résumé"),
        ("note", "Done: Resume_Petro_Kravchenko.pdf (see the list of changes in the lesson of 21/10)."),
        ("h2", "3. Feedback on Module 1"),
        ("todo", "Fill in the Google Form (forms.gle/rVzhnjAjrj8dtcvp9) with your own opinion."),
        ("h2", "4. A video of my pitch"),
        ("p", "The script is in the file “Pitch_script_Petro_Kravchenko” (about 80 seconds)."),
        ("todo", "Record the video yourself (camera at eye level, plain background, good light, speak slowly) "
                 "and send it to the teacher."),
        ("h2", "5. Teamwork: Benefits of using LinkedIn — Personal Branding, Career Growth & Development"),
        ("p", "Group: Denys, Nastia B., Yehor, Petro. My notes for our part of the presentation:"),
        ("linkedin", None),
        ("h2", "6. Grammar exercise: “The Intern — The Video Résumé” (listeninenglish.com)"),
        ("p", "**Questions:**"),
        ("table", ["Question", "Answer"], [
            ["What does Ben say about himself?", "He is retired; he has lots of free time; he has travelled "
                                                 "around the world. (Not true: his wife died 3.5 years ago, not "
                                                 "a few months ago; he is not unhappy.)"],
            ["Where does he go in the morning?", "To Starbucks."],
            ["What has Ben tried to keep busy?", "Golf, yoga, cooking (“learned to cook”), language classes "
                                                 "(Mandarin)."],
            ["Why does Ben go to San Diego?", "To see his family."],
            ["How does Ben feel about his family?", "They are great; he depends on them too much."],
            ["What did Ben see in the market?", "A flyer for an intern job."],
            ["What are the requirements for the job?", "Over 65; an interest in e-commerce; hard-working (also: "
                                                       "organisational skills)."],
            ["What type of company is it?", "It sells clothing online."],
            ["How can he apply for the job?", "He must submit a video."],
            ["Why does he want the job?", "He wants to be needed, to keep busy and to have new challenges."],
            ["What will be most difficult for Ben?", "Dealing with technology."],
        ], [6.0, 10.0]),
        ("p", "**Vocabulary review:** 1 playing hooky from; 2 come rain or shine; 3 with a roll-up-your-sleeves "
              "attitude; 4 hit him like a ton of bricks; 5 out of the corner of his eye."),
        ("p", "**Grammar (prepositions):** some time **on** my hands; gone **for** three and a half years; "
              "travelled **—** the globe; the key **to** this whole deal; I'm **at** my Starbucks **by** 7:15; "
              "looking **for** senior interns; sell clothes **on** the Internet; upload your video **to** "
              "YouTube; I'll get **—** there; good **in** a crisis; right **—** here **in** Brooklyn; I've "
              "lived **—** here; live **in** Brooklyn; help **with** that."),
        ("p", "**Sentence building (present time frame):**"),
        ("num", [
            "Ben is retired, and his wife died three and a half years ago.",
            "At first, he enjoyed being retired.",
            "He goes to Starbucks every day at 7:15, come rain or shine.",
            "Ben has taken up many hobbies to keep busy.",
            "These days, he only travels to San Diego to visit his son and his family.",
            "Ben feels that there is a hole in his life that he needs to fill.",
            "Ben sees a flyer for an Internet company that is advertising for senior interns.",
            "The job is for a company that sells clothing online.",
            "Ben has to upload a video cover letter to YouTube.",
            "Ben thinks that the job is a good idea because he wants more excitement in his life.",
            "Ben says that he is eager to learn.",
            "Ben thinks that he might not be hip enough to live in Brooklyn.",
        ]),
        ("p", "**Discussion.** *Six things Ben did after his wife died:* he travelled the globe, went to Starbucks "
              "every morning, played golf, tried yoga, learned to cook and took classes in Mandarin (he also "
              "read books, watched movies and bought plants). *Would I hire Ben?* Yes, for a role with people: "
              "his strengths are experience, loyalty, being trustworthy and good in a crisis; his weakness is "
              "technology, but he is eager to learn. *“I still have music in me”* means that he still has "
              "energy and something valuable to give, so he is not ready to stop working. *Video résumé:* it "
              "shows personality and communication skills, but it takes more time to watch than a paper "
              "résumé, an ATS cannot scan it, and it may lead to bias based on appearance."),
        ("h2", "7. Test: Cover Letter Vocabulary 2 (businessenglishsite.com)"),
        ("table", ["#", "Answer", "#", "Answer"], [
            ["1", "previous", "6", "course"],
            ["2", "instilled", "7", "a valuable"],
            ["3", "fluent", "8", "earliest"],
            ["4", "understanding", "9", "from the"],
            ["5", "verbal", "10", "promoting"],
        ], [1.2, 6.8, 1.2, 6.8]),
        ("h2", "8. Extra: my cover letter"),
        ("note", "Written for the Rangein Junior DevOps Engineer vacancy — see the file "
                 "“Cover_letter_Petro_Kravchenko”."),
    ]),
]

LINKEDIN_TALK = [
    ("Why LinkedIn?",
     "LinkedIn has more than **1 billion members in more than 200 countries and territories** (LinkedIn, "
     "about.linkedin.com). Its mission is to “connect the world's professionals to make them more productive "
     "and successful”. For a student, it is the easiest way to get the ball rolling with a career."),
    ("Personal branding",
     "Your personal brand is what people think of you as a professional. On LinkedIn you build it with a "
     "**professional photo**, a clear **headline** (for example, “Junior DevOps & Network Engineer | Docker · "
     "Linux · Cisco”), an **About** section that works like the summary in a résumé, and a **Featured** section "
     "with your best projects. When colleagues **endorse** your skills and write **recommendations**, recruiters "
     "see that other people trust you."),
    ("Career growth",
     "Recruiters search LinkedIn every day, so a complete profile works for you come rain or shine. You can "
     "turn on **Open to Work**, set **job alerts**, follow companies you like and contact alumni of your "
     "university. A network of real professionals often brings opportunities that are never advertised."),
    ("Development",
     "LinkedIn is also a place to learn: you can follow experts, read posts and articles about your field, join "
     "groups and events, and take courses on **LinkedIn Learning**. Adding new certificates to the **Licenses & "
     "certifications** section shows that you are eager to learn."),
    ("My plan",
     "I will update my headline and About section with the text of my new résumé, add the campus network and "
     "Luxora projects to Featured, list my Cisco and Oracle certificates, and ask my teammates to endorse my "
     "Docker and networking skills."),
]

SOURCES = [
    ("WGN News. Job & Career Advice for Young People (video, 04.02.2025)", "https://www.youtube.com/watch?v=SryD1az3sL4"),
    ("BBC News. Six essential skills employers say job seekers should have to stand out",
     "https://www.bbc.com/news/articles/cn9n9n5p9eqo"),
    ("English with Lucy. Tell Me About Yourself — An Excellent Answer to this Interview Question (video)",
     "https://www.youtube.com/watch?v=xLzy3-CQIls"),
    ("Resume Genius. CV vs Resume: What's the difference? (video)", "https://www.youtube.com/watch?v=UKKzWkbuS44"),
    ("Timothy Lewis. Interesting Facts About Resume Writing: What You Need to Know to Stand Out (LinkedIn)",
     "https://www.linkedin.com/pulse/interesting-facts-resume-writing-what-you-need-know-stand-lewis-mxmke/"),
    ("Life at Google. Create Your Resume for Google: Tips and Advice (video)",
     "https://www.youtube.com/watch?v=BYUy1yvjHxE"),
    ("Legendary Investors. Warren Buffett and Charlie Munger Explain Circle of Competence (video)",
     "https://www.youtube.com/watch?v=0KHfRO2EnyA"),
    ("Speak Confident English. Cover Letters vs. Resumes and How to Write a Cover Letter in English (video)",
     "https://www.youtube.com/watch?v=Wy1ywzSGa74"),
    ("Listen in English. The Intern — The Video Résumé", "https://www.listeninenglish.com/ve148-the-intern-video-resume.php"),
    ("Business English Site. Cover Letter Vocabulary 2", "https://www.businessenglishsite.com/exercise_coverletter2.html"),
    ("LinkedIn. About LinkedIn", "https://about.linkedin.com/"),
] + [(f"Djinni. {v['role']} — {v['company']}", v["url"]) for v in VACANCIES]
