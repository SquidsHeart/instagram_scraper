This project is a simple instagram scraper, designed for making info gathering iteratively on an instagram account easier.

Initiate the class through scraper(put username here, put password here) and then make use of the wide range of functions(finding followers, following, mutuals, etc.)

Most functions(barring the common_following and common_follower functions) make use of the unique user id, which can be found through the "find_user_data" function. This returns a dictionary, which also has followers, following, posts, email address(if applicable), phone number("if applicable") and whether the account is public.

common_following and common_follower both take lists as their values.

