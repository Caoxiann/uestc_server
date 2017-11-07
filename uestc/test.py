from uestc import login, query
login_session = login('2015060108002', '513121')
courses = query.get_course(login_session)
print(courses)
