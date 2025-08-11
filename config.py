# --- Sourcing & Scoring Configuration ---
# The exact job title you want to search for on LinkedIn
SEARCH_JOB_TITLE = 'Norway (C++)'
# The maximum number of candidate URLs to collect from the search.
MAX_CANDIDATES_TO_FIND = 25

# The full job description (used for scoring)
JOB_DESCRIPTION = """

About the Company:
Kratos is the leading provider of satellite Control and Monitoring solutions, with 80% market share. Kratos is also a leading actor in modernizing SatCom ground infrastructure, by developing a new generation of software-defined Satellite Communication products based on Kratos OpenSpace® Platform. OpenSpace® utilize cutting-edge cloud technologies, optimized for  maximum flexibility and performance.
Kratos Norway is the Center of Excellence for VSAT technology within the Kratos group and has 20 years of track record developing highly efficient and advanced solutions for the satellite ground segment.
Kratos Norway is now looking for Software Developers to contribute to the development of the next generation of digital and virtualized satellite monitoring and communication products.

Key Responsibilities:

Development of software communication and monitoring products
Design, architecture and documentation
Collaboration with other Kratos teams (mainly in the US)
Supporting other parts of the organization (sales, delivery, customer support)
Support execution of agile and scrum processes

Requirements:
Higher technical education within software development, preferably a Master’s degree
Significant and documented experience in software design and development
Object-oriented programming background, preferably in C++
Experience with distributed systems built on Docker and Kubernetes
Experience with communication protocols such as TCP/IP, DVB, or 3GPP
Experience with Scrum and agile development processes and tools
Fluency in written and spoken English

Qualifications:
Result-oriented, methodical, and structured
Strong team player with good communication skills
What the Company Offers
Work with state-of-the-art technology with cutting-edge products and advanced solutions for the satellite communication industry
Open and informal organization
An international and engaging work environment
Flexible working hours
Competitive terms, including health insurance, travel insurance and good pension schemes
"""

# Weights for the final Lead Score calculation. We can Adjust these weights as needed.
LEAD_SCORE_WEIGHTS = {
    'relevance': 0.5,
    'tenure': 0.3,
    'activity': 0.2
}

# Keywords that must be present in a candidate's "Current Role" to be considered.
# The script checks if all keywords in this list are present in the role string.
# The check is case-insensitive.As expert recruiters, include the necessary keywords that are essential for the role.
REQUIRED_KEYWORDS = []
