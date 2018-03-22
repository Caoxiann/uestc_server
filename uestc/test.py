from uestc import login, query
d = login('2015060108002', '513121')
login_session = d["session"]
print(d["name"])
scores = query.get_all_socre(login_session, '2015060108002')
print(scores.__len__())