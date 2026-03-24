This project contains two parts:
1. Part one: Google Play Store reviews analyzer of groww app.
2. Part B: Fee explainer (exit load)

In part A, The project :
- scrapes the reviews from play store
- Stores in csv
- Generates themes
- Classifies reviews into themes
- Generates insights (Theme summary and actionables)
- Generates a mail body and PDF
- Sends the mail

Part B: The project:
- scrapes the exit loads of three mutual fund schemes
- takes the definition from an official website about what exit load is
- generates three to five bullet points regarding this data
- attaches this content in the mail body 
- Sends the mail

Both part A and part B are attached in the same mail, and via MCP, the JSONs generated in part A and part B are appended or updated in a Google Doc. 
In the mail, the content is of both the parts in the mail body, and there is a CTA to view Google Docs where the combined JSON of part A and part B is present. Also, there is an attachment in the mail, a PDF, where more details, like sample reviews under each theme, are mentioned. 

The entire pipeline can be triggered both manually and via scheduler. The scheduler runs every four hours in a day. 

Deployement Links

FE - https://app-reviews-analyzer.vercel.app/

BE - https://app-reviews-analyzer-1.onrender.com/

Json DOC Link: https://docs.google.com/document/d/1sA4e68KZOm3ovauae7pgAsj0al4b5bq1BdkaUGc6oPk/edit?tab=t.0



Part A Sources:

https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN

Part B Sources:

https://groww.in/mutual-funds/axis-flexi-cap-fund-direct-growth

https://groww.in/mutual-funds/nippon-india-large-cap-fund-direct-growth

https://groww.in/mutual-funds/icici-prudential-indo-asia-equity-fund-direct-growth

https://www.miraeassetmf.co.in/knowledge-center/exit-load-in-mutual-funds



