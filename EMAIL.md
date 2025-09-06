

We would like the ability to add email campaigns to our platform. A campaign has a name, and a list which mus contain an email address, a subject line, and a google doc which contains the text of the email. Each campaign should create a row in a firestore database with that tuple, and should assign a 'campaign id'. It should refer to the list by the list_id, and store a link to the document.

We will integrate into sendgrid for the sending of emails. We will then use their 'event tracking' APIs to track back to individuals in our data schema to track which individuals (as known by master_id) took various actions for a given campaign (as known by its campaign id).

We need a campaign manager tool (there's already a button for it on the left nav) to bring up a screen that allows for a user to select a campaign (or multiple of them )from the list of campaigns, and then shows the event statistics for those campaigns (clicks, email opens, and clickthroughs).


