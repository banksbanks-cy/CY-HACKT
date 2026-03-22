from app.utils.text_cleaner import clean_html

test = "<p>Hello <b>world</b> &amp; hackers</p>"

print(clean_html(test))
