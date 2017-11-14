from uestc import login, query
d = login('2015060108002', '513121')
login_session = d["session"]
print(d["name"])
scores = query.get_course(login_session, "2017-2018-1")
print(scores)
