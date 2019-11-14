# Project 1, Part 3

Authors: Tomas Larrain (tal2150), Lawan Rahim (lr2965)

PostgreSQL database (user) to grade: tal2150

Project URL: http://35.196.65.227:8111

URL of the web application: 

## Implemented elements of Part 1:

All, in particular:

- General search bar 
- Advanced search
- Each paper is clickable to obtain e.g. the repository url if available
- Information on authors (to get in touch with) and institutions are available 
- Log-in and Registration page
- User History (substituted the user favorites)
- Simple Recommender system (log-in required)
- Organized Menu (with Models and Applications to explore)

## Changes that have been made to the proposal in part1 and/or part2:

The attribute name date_published of the table repositories has been changed to rdate_published. The TA has been informed on this change. Moreover, we have listed the full User History which replaces the user's favorites. This way the user has access to all the papers s/he has read.   

## Two interesting web pages of our web application: 

1. Advanced Search: 

The first interesting web page of our web application is also the one that highlights the goal behind our 
database the most. With the advanced search, the user is able to query our database in a user-oriented way. 
The interface provides several input fields which are incorporated into SQL queries to tailor the search to the user's interests. For instance, a doctor who would like to learn about machine learning applications for cancer prediction can easily specify the context and moreover, select the programming language they are most familiar with. This gives novices a powerful tool to benefit from machine learning in an easy way. 

2. Home page (while logged-in):

The next interesting page is the home page when the user is logged in. This is because of two reasons. First, the
user receives tailored recommendations of new papers from an SQL based recommender system which makes use of the keywords related to previous queries. Second, the home page offers a menu divided into models and applications. These can be explored in case the user has no specific research fields in mind, but rather wants to explore some topics on machine learning. For instance, the user might have heard about Deep Learning and is now curious to see which applications have made use of this method and how the results turned out to be. Again, most of our components are connected so that the user can easily find a repository linked to a certain paper or the author, possibly in view of collaborations. 




