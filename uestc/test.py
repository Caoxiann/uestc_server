from uestc import login, query
login_session = login('2015060108002', '513121')
scores = query.get_course(login_session, "2017-2018-1")
print(scores)
