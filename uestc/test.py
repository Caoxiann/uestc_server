from uestc import login, query
login_session = login('2015060108002', '513121')
scores = query.get_all_socre(login_session, '2015060108002')
print(scores)
