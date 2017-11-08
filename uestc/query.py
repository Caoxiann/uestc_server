# -*- coding:utf-8 -*-
"""查询信息"""
import json
from .exceptions import QueryError
from bs4 import BeautifulSoup
import time
import re
__all__ = ['get_now_semesterid', 'get_semesterid_data', 'get_score', 'course_info']

course_pattern = re.compile(r'TaskActivity\((.*)\)([^T]*)')
info_pattern = re.compile(r'"(.*?)",?' * 7)
time_pattern = re.compile(r'index =(\d+)\*unitCount\+(\d+);')
name_pattern = re.compile('.*\(([^)]*)\)')


def __get_mid_text(text, left_text, right_text, start=0):
    """获取中间文本"""
    left = text.find(left_text, start)
    if left == -1:
        return ('', -1)
    left += len(left_text)
    right = text.find(right_text, left)
    if right == -1:
        return ('', -1)
    return (text[left:right], right)


def get_score(login_session, semester):
    """查询成绩
    semester样例：2015-2016-2
    返回一个list的嵌套
    格式为
    [[学年学期,课程代码,课程序号,课程名称,课程类别,学分,总评成绩,补考总评,最终,绩点]]"""
    semesterid_data = get_semesterid_data(login_session)
    response = login_session.get('http://eams.uestc.edu.cn/eams/teach/grade/course/person!search.action?semesterId=%d' % semesterid_data[semester])
    soup = BeautifulSoup(response.text, 'html.parser')
    result = soup.find_all('td')
    ret = []

    for i in range(len(result)):
        if result[i].string:
            result[i].string = result[i].string.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')
    for i in range(len(result) // 10):
        ret.append(result[i * 10 : i * 10 + 10])
        for j in range(len(ret[i])):
            ret[i][j] = ret[i][j].string

    return ret


def get_all_socre(login_session, userid):
    semesters = get_semesterid_data(login_session)
    now_semesid = get_now_semesterid(login_session)
    now_semes = None
    for key, value in semesters.items():
        if value == now_semesid:
            now_semes = key
    fresh_year = int(userid[:4])
    count = 0
    scores = []
    while fresh_year < int(now_semes[:4]):
        semes = str(fresh_year) + '-' + str(fresh_year + 1) + '-' + str((count % 2) + 1)
        fresh_year += (count % 2)
        count += 1
        scores.append(get_score(login_session, semes))
    return scores


def get_now_semesterid(login_session):
    """获取当前semesterid并返回int 失败则抛出异常"""
    response = login_session.get('http://eams.uestc.edu.cn/eams/teach/grade/course/person.action')
    data = __get_mid_text(response.text, 'semesterId=', '&')
    if data[1] == -1:
        raise QueryError('当前semesterid获取失败')
    ret = int(data[0])
    return ret


def get_semesterid_data(login_session):
    """获取学期对应的semesterid信息 成功则返回dict"""
    post_data = {
        'dataType':'semesterCalendar',
    }
    # 将得到的数据转换为json
    response = login_session.post('http://eams.uestc.edu.cn/eams/dataQuery.action', post_data)
    response_text = response.text
    response_text = response.text.replace('yearDom', '"yearDom"')
    response_text = response_text.replace('termDom', '"termDom"')
    response_text = response_text.replace('semesters', '"semesters"')
    response_text = response_text.replace('schoolYear', '"schoolYear"')
    response_text = response_text.replace('id', '"id"')
    response_text = response_text.replace('name', '"name"')
    response_text = response_text.replace('yearIndex', '"yearIndex"')
    response_text = response_text.replace('termIndex', '"termIndex"')
    response_text = response_text.replace('semesterId', '"semesterId"')
    i = 0
    while True:
        if response_text.find('y' + str(i)) != -1:
            response_text = response_text.replace('y%d' % i, '"y%d"' % i)
            i += 1
        else:
            break
    # json转为dict并提取为有用的数据
    try:
        semesterid_data = json.loads(response_text)['semesters']
    except json.decoder.JSONDecodeError:
        raise QueryError('当前账户登录已过期，请重新登录')
    ret = {}
    for i in semesterid_data:
        for j in semesterid_data[i]:
            ret.update({'%s-%s' % (j['schoolYear'], j['name']):j['id']})
    return ret


def get_course(login_session, semester=None):
    if semester:
        semester_id = get_semesterid_data(login_session).get(semester)
    else:
        semester_id = get_now_semesterid(login_session)

    time_stamp = time.time()
    print(int(round(time_stamp * 1000)))
    url = 'http://eams.uestc.edu.cn/eams/courseTableForStd.action?_=' + str(time_stamp)
    resp = login_session.get(url)
    # print(resp.text)
    return step1(login_session, resp.text, semester_id)


def step1(login_session, source_text, semesterid):
    if not semesterid:
        semesterid = get_now_semesterid(login_session)
    ids = re.findall('ids.*\)', source_text)[0]
    ids = re.findall('\d+', ids)[0]
    return course_info(login_session, ids, semesterid)


def course_info(login_session, ids, semesterid=None):
    url = 'http://eams.uestc.edu.cn/eams/courseTableForStd!courseTable.action?ignoreHead=1&setting.kind=std&startWeek=1&semester.id=' + str(semesterid) + '&ids=' + str(ids);
    resp = login_session.get(url)
    courses = []
    for match in course_pattern.finditer(resp.text):
        course = {}
        info = info_pattern.search(match.group(1))
        courseid = re.findall(r'[^()]+', info.group(4))[1]
        course_name = re.sub('\(.*?\)', '', info.group(4))
        course['teacher_id'] = info.group(1)
        course['teacher_name'] = info.group(1)
        course['course_id'] = courseid
        course['course_name'] = course_name
        course['room_id'] = info.group(5)
        course['room_name'] = info.group(6)
        course['weeks'] = tuple(i for i, v in enumerate(info.group(7)) if v == '1')
        course['time'] = []
        t = time_pattern.findall(match.group(2))
        for weekday, clss in t:
            course['time'].append((int(weekday) + 1, int(clss) + 1))
        courses.append(course)
    return courses

'''
def step2(login_session, ids):
    semester = get_now_semesterid(login_session)
    url = 'http://eams.uestc.edu.cn/eams/courseTableForStd!courseTable.action?ignoreHead=1&setting.kind=std&startWeek=1&semester.id=' + str(semester) + '&ids=' + str(ids);
    resp = login_session.get(url)
    tmp = re.findall(r'activity = new TaskActivity.*activity', resp.text, re.DOTALL)[0].split('activity =')

    data = []

    for value in tmp:
        if value.__len__():
            info = re.findall('TaskActivity\((.*)\)', value, re.DOTALL)[0].replace('\"', '').split(',')
            tmptime = re.findall('index =.*?\;', value)

            times = []
            for t in tmptime:
                times.append(re.findall('\d+', t))

            data.append({
                "info": info,
                "time": times
            })
    courses = []
    for v in data:
        print(v)
        course = {
            "courseName": v['info'][3],
            "courseID": v['info'][3],
            "teacher": v['info'][1],
            "room": v['info'][5],
            "time": v['time'],
            "date": parse_time_string(v['info'][6])
        }
        courses.append(course)
        print(course)


def parse_time_string(string):
    res = []
    matchFullWeek = re.compile('1{2,}')
    matchSingleWeek = re.compile('(10){2,}')

    full_week = match_str(matchFullWeek, string)
    single_week = match_str(matchSingleWeek, full_week[1])

    for v in full_week[0]:
        start_week = str(v.start())
        end_week = str(v.end() - 1)
        res.append(start_week + '-' + end_week + '周')

    for v in single_week[0]:
        start_week = str(v.start())
        end_week = str(v.end() - 1)
        attr = '单'
        if start_week % 2 == 0:
            attr = '双'
        else:
            attr = "单"
        res.append(start_week + '-' + end_week + attr + '周')
    print(full_week, single_week, res)
    return res


def match_str(pattern, str):
    tmpRes = []
    tmp = None
    tmpStr = str
    while True:
        tmp = pattern.search(tmpStr)
        if tmp:
            tmpRes.append(tmp)
            tmpStr = tmpStr.replace(tmp[0], get_zero_str(tmp[0].__len__()))
        else:
            break
    return [tmpRes, tmpStr]


def get_zero_str(num):
    zeros = ''
    num -= 1
    while num > 0:
        zeros += '0'
        num -= 1
    return zeros
'''


'''
def save_score(file_name, score_data):
    """保存成绩"""
    try:
        os.remove(file_name)
    except Exception:
        pass
    workbook = xlsxwriter.Workbook(file_name)  #创建一个excel文件
    worksheet = workbook.add_worksheet()
    text = ['学年学期', '课程代码', '课程序号', '课程名称', '课程类别', '学分', '总评成绩', '补考总评', '最终', '绩点']
    for i in range(len(text)):
        worksheet.write(0, i, text[i])
    for i in range(len(score_data)):
        for j in range(len(score_data[i])):
            worksheet.write(i + 1, j, score_data[i][j])
    worksheet.set_column(0, len(score_data[i]), 15)
    workbook.close()


# 参数设置
parser = optparse.OptionParser()
parser.add_option('-n', '--num',
                  help='学号')
parser.add_option('-p', '--password',
                  help='密码')
parser.add_option('-t', '--time',
                  help='每次查询的延时 单位为秒')
parser.add_option('-s', '--semester',
                  help='学期 如 2016-2017-1')
parser.add_option('-a', '--all', action="store_true",
                  help="查询所有")
parser.add_option('-A', '--always', action="store_true",
                  help="一直查询")
(__options__, __args__) = parser.parse_args()
print(__options__)
if __options__.num is None:
    __options__.num = input('请输入你的学号:')
if __options__.password is None:
    __options__.password = getpass.getpass('请输入你的密码:')
while True:
    if __options__.semester is not None:
        if len(__options__.semester.split('-')) == 3:
            break
    __options__.semester = input('请输入你的学期:')
# 全局常量
URL = (
    'http://eams.uestc.edu.cn/eams/teach/grade/course/person.action',
    'http://eams.uestc.edu.cn/eams/dataQuery.action',
    'http://eams.uestc.edu.cn/eams/teach/grade/course/person!search.action?semesterId=%d'
)


#登陆
__session__ = uestc_login.login(__options__.num, __options__.password)
if __session__ is None:
    print('登陆失败')
    print(uestc_login.get_last_error())
    exit()
print('登陆成功')


#初始化查询
print('初始化查询...', end='')
__now_semesterid__ = get_now_semesterid(__session__)
__semesterid_data__ = get_semesterid(__session__, __now_semesterid__)
print('[OK]')

#查询
if __options__.always:
    start_query_score(__session__, __options__.semester)
else:
    print('查询.........', end='')
    __score_data__ = query_score(__session__, __options__.semester)
    save_score('out.xlsx', __score_data__)
    print('[OK]')
    print('数据已写入out.xlsx')
    #send_message(__score_data__, ['plusls@qq.com'])
'''