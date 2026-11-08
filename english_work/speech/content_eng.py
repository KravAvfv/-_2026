"""Суфлер і сценарій для «Англійська мова» — Job Getting Course (ICT-31): what to say in class, in English.
Facts = english_work/content.py (résumé, vacancies, video answers)."""

SPEECHES = [
    dict(
        id="Elevator_pitch",
        title="Elevator pitch (60–90 seconds)",
        notation="Pitch: self-introduction → key skills → achievements → problems I can solve → call to action",
        show="Pitch_script_Petro_Kravchenko.pdf; Homework portfolio, Lesson 3 (23/09)",
        role="The video homework of 28/10 and the opening of any interview or networking talk.",
        opening=["Speak slowly, look at the camera or the teacher, and make a short pause after each of the "
                 "five parts. The full text is in the pitch script; below are the key points only."],
        walk=[
            "**Who I am:** Petro Kravchenko, junior DevOps and network engineer, third-year Information Systems "
            "and Technologies student at Taras Shevchenko National University of Kyiv.",
            "**Key skills:** proficient in Docker, Linux and Nginx; experienced in Cisco networking — VLANs, "
            "routing, network security; familiar with Python, SQL, Grafana and Prometheus.",
            "**Achievements:** a three-tier campus network for **700+ users**; the Luxora website "
            "(Germany) — containerised with Docker, running on a Linux server behind Nginx; an ISO 27001-based "
            "audit and a penetration test for a commercial client.",
            "**Problems I solve:** infrastructure that is fast, secure and easy to maintain — from the network "
            "to the container.",
            "**Call to action:** “I look forward to demonstrating how I can add value to your team. Let's talk!”",
        ],
        traps=[
            ("Why DevOps and not software development?",
             "I like the moment when code becomes a working service. I enjoy Linux, containers and networks more "
             "than writing features, and my network background helps me in DevOps."),
            ("What exactly did you do in the campus network project?",
             "I designed a three-tier network — core, distribution and access — for 700+ users: VLANs, inter-VLAN "
             "routing, STP, redundant uplinks, port security, DHCP snooping, DAI and ACLs, plus full documentation."),
            ("What is your weakness?",
             "I don't have much commercial experience yet, and I'm still learning cloud and CI/CD tools. That's "
             "why I'm doing the Mate Academy DevOps track."),
            ("What is your level of English?",
             "B1, Intermediate. I read technical documentation every day and I want to reach B2."),
        ],
        defense=["If you forget a line, go to the next part of the structure: skills → achievements → call to "
                 "action. The teacher grades the structure and the vocabulary, not a word-for-word text."],
    ),
    dict(
        id="Resume",
        title="My final résumé: structure and changes",
        notation="Résumé sections: photo, contacts, summary, experience, skills, education, languages; "
                 "achievements = action verb + tool + result + number",
        show="Resume_Petro_Kravchenko.pdf; Homework portfolio, Lesson 8 (table of changes) and Lesson 7 (ATS check)",
        role="Homework of 14/10, 21/10 and 28/10: submit the final version and explain the improvements.",
        opening=["“This is the final version of my résumé. I made it one page, ATS-friendly and focused on "
                 "DevOps and networking.”"],
        walk=[
            "**Header:** photo, name, job title “Junior DevOps & Network Engineer”, city, email, phone, LinkedIn.",
            "**Profile:** four sentences — who I am, what I offer, what value I bring.",
            "**Experience & Projects** in reverse chronological order; current roles in the base form (Develop, "
            "Build), finished ones in the past tense (Designed, Performed).",
            "**Skills** grouped: Networking, DevOps, Security, Development, Currently learning.",
            "**Education & Certifications** with the expected graduation year (2028) and GPA; **Languages:** "
            "Ukrainian native, English B1.",
            "**Changes:** fixed the job title, added Languages, Arial instead of a decorative font, removed logos, "
            "one column; ATS check — 15 of 20 Rangein keywords.",
        ],
        traps=[
            ("Why did you remove the logos?",
             "An Applicant Tracking System cannot read images, so logos take space but give nothing. I kept only "
             "the photo, because the course requires it."),
            ("Why are some verbs in the present and some in the past?",
             "That's the rule from our lesson: the base form for the current job (Develop, Build) and the past "
             "tense for finished work (Designed, Performed)."),
            ("Why don't you have more numbers in your achievements?",
             "I used only numbers that I can prove, like 700+ users. I don't want to invent percentages; when I "
             "measure results at Luxora, I will add them."),
            ("Which keywords are missing, and why didn't you add them?",
             "DNS, HTTP, GCP, Ansible and GitHub Actions. I didn't add them artificially — that would be keyword "
             "stuffing. These are skills I'm still learning."),
        ],
        defense=["“The Google formula is ‘Accomplished X as measured by Y, by doing Z’ — for example, ‘Designed "
                 "a 3-tier network for 700+ users using VLANs, STP and redundant uplinks’.”"],
    ),
    dict(
        id="Cover_letter",
        title="Cover letter for the Rangein vacancy",
        notation="Cover letter: business letter, conversational tone, keywords, 3–4 paragraphs, one page",
        show="Cover_letter_Petro_Kravchenko.pdf; Homework portfolio, Lesson 8 (video questions) and Lesson 9 (test)",
        role="Topic of 21/10 and 28/10: the difference between a résumé and a cover letter, the four tips.",
        opening=["“My cover letter is for the Junior DevOps Engineer vacancy at Rangein from Djinni. It follows "
                 "the four tips from the Speak Confident English video.”"],
        walk=[
            "**Paragraph 1 — introduction:** how I found the position and why it interests me.",
            "**Paragraph 2 — value and one story:** Docker, Linux and Nginx at Luxora — the keywords of the "
            "vacancy.",
            "**Paragraph 3 — explaining a gap:** less than 1–2 years of commercial experience, but network and "
            "security projects and the Mate Academy DevOps track.",
            "**Paragraph 4 — closing with a call to action:** “I would welcome the opportunity to discuss how I "
            "can contribute to your team.”",
        ],
        traps=[
            ("How is a cover letter different from a résumé?",
             "A résumé is objective — facts in bullet points, without “I”. A cover letter is subjective — it "
             "explains why I'm the right fit, in paragraphs, with “I” and “you”, and tells one story."),
            ("Why “Dear Hiring Manager”?",
             "The video says to use the person's name; the vacancy doesn't give one, so I used the recommended "
             "alternative instead of “To whom it may concern”."),
            ("When do you need a cover letter?",
             "When the vacancy asks for it, when someone referred you, when you need to explain something (a "
             "gap or a different background), or when you change your career field."),
            ("Answers of the cover-letter test?",
             "previous, instilled, fluent, understanding, verbal, course, a valuable, earliest, from the, "
             "promoting."),
        ],
        defense=["The letter is one page and doesn't repeat the résumé — that's tip number four."],
    ),
    dict(
        id="LinkedIn_teamwork",
        title="Teamwork: LinkedIn — Personal Branding, Career Growth & Development",
        notation="Group: Denys, Nastia B., Yehor, Petro",
        show="Homework portfolio, Lesson 9 (28/10), section 5",
        role="My part of the group presentation on the benefits of using LinkedIn.",
        opening=["“LinkedIn has more than one billion members in more than two hundred countries and "
                 "territories. For a student, it's the easiest way to get the ball rolling with a career.”"],
        walk=[
            "**Personal branding:** professional photo, headline, About section, Featured projects; skills "
            "endorsed by colleagues and recommendations.",
            "**Career growth:** recruiters search LinkedIn every day; Open to Work, job alerts, following "
            "companies, contacting alumni.",
            "**Development:** following experts, groups and events, LinkedIn Learning, the Licenses & "
            "certifications section.",
            "**My plan:** new headline and About from my résumé, projects in Featured, Cisco and Oracle "
            "certificates, endorsements for Docker and networking.",
        ],
        traps=[
            ("What is a personal brand?",
             "It's what people think of you as a professional — your image based on your profile, posts and "
             "what others say about you."),
            ("What does “to endorse” mean?",
             "To publicly support or recommend someone — on LinkedIn, colleagues endorse your skills."),
            ("Is LinkedIn useful for a student with little experience?",
             "Yes: you can show projects in Featured, add certificates and connect with alumni and recruiters "
             "before you graduate."),
        ],
        defense=["Agree the split of the four parts with Denys, Nastia B. and Yehor before the lesson; the notes "
                 "cover the whole topic, so any part can be mine."],
    ),
    dict(
        id="Job_search_discussion",
        title="Discussion topics: job search, skills, CV vs résumé, circle of competence",
        notation="Videos and articles of 09/09–14/10; vacancy analysis",
        show="Homework portfolio, Lessons 1, 3, 4, 7",
        role="Be ready to discuss the reading and video homework in class.",
        opening=["Use one fact from the source and one sentence about yourself for every answer."],
        walk=[
            "**WGN video (09/09):** dream career, not one dream job; the “seven stories” method; breadth, not "
            "only depth.",
            "**BBC article (09/09):** six NFER skills — organising, problem solving, communication, "
            "collaboration, creative thinking, information literacy; 42% of employers name a lack of soft skills.",
            "**Vacancies (23/09):** Rangein, RedCore, Kyivstar.Tech — common requirements: Linux, Docker, Git, "
            "CI/CD, scripting, networking, monitoring; English B1–B2.",
            "**CV vs résumé (26/09):** in the USA a résumé is for jobs and a CV is academic; in the UK and Europe "
            "“CV” is used for both.",
            "**Circle of competence (14/10):** know the perimeter of your circle; Mrs B knew what she didn't "
            "know; mine: Linux, Docker, Cisco — learning: CI/CD, Terraform, cloud.",
        ],
        traps=[
            ("Which of the six skills is the most important for IT?",
             "Problem solving, because DevOps work is mostly about finding the cause of a problem and fixing it; "
             "but communication is next, because the team must understand the solution."),
            ("What surprised you in the article about résumé facts?",
             "That recruiters spend only six or seven seconds on a résumé. So I put my title and key skills at "
             "the top."),
            ("What does “Getting a job is a job in itself” mean?",
             "Looking for a job takes as much time and effort as real work: research, tailoring the CV, cover "
             "letters, interviews."),
            ("Which vacancy suits you best and why?",
             "Rangein: it's remote, and its requirements — Docker, Linux, Nginx, Bash or Python — match my "
             "experience. My gap is cloud and CI/CD tools."),
        ],
        defense=["The Esther video answers (Lesson 4) are left as lines to complete in class — the coursebook "
                 "video is not available online."],
    ),
]

DEMO = dict(
    minutes=6,
    intro="Open the homework portfolio and the three attached files. Speak English the whole time; start with "
          "the pitch, then show the résumé and the other materials.",
    steps=[
        ("Pitch", "Pitch_script_Petro_Kravchenko.pdf (or play the recorded video)",
         "Give the pitch in five parts — about 80 seconds."),
        ("Résumé", "Resume_Petro_Kravchenko.pdf", "“This is my final résumé — one page, ATS-friendly.” "
         "Walk through the sections from top to bottom."),
        ("What I changed", "Homework portfolio, Lesson 8 — table of changes; Lesson 7 — ATS check",
         "Name three changes: job title, Languages section, no logos; 15 of 20 keywords."),
        ("Cover letter", "Cover_letter_Petro_Kravchenko.pdf", "Explain the four paragraphs and the difference "
         "between a résumé and a cover letter."),
        ("LinkedIn", "Homework portfolio, Lesson 9, section 5", "Present my part: personal branding, career "
         "growth, development, my plan."),
        ("Other homework", "Homework portfolio: contents page, then any lesson the teacher asks for",
         "Answers to the exercises, video notes and the vocabulary bank with my examples."),
    ],
    finish="“Thank you! I'm ready to answer your questions.” Things still to do personally: Codecademy quiz "
           "screenshot, Module 1 feedback form, the pitch video, sending the résumé via Telegram.",
)
