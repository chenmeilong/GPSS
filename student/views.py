# student APP

from django.shortcuts import render
from django.shortcuts import render, HttpResponse, redirect
import json
from manager import models
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.db.models import Q


def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        ret = {'status': True, 'error': None}
        try:
            user_code = request.POST.get('stu_username', None)  # 沒有则为空
            password = request.POST.get('stu_password', None)
            remember = request.POST.get('stu_remember', None)  # 这是Ture 记住密码or falase不记住
            print("学号:", user_code)
            print("密码:", password)
            # print("记住密码:", remember)
            obj = models.UserTable.objects.filter(user_code=user_code, user_type='0').first()  # 找到用户  且用户为学生
            if obj:
                if obj.user_stat == "1":
                    if obj.user_password == password:
                        request.session['is_login'] = True
                        request.session['user_code'] = user_code
                        request.session['user_type'] = '0'  # 在session写入用户的类型  给与不同用户不同的权限
                        request.session.set_expiry(24 * 60 * 60)  # 一天免登陆
                        if remember == "True":
                            # session中设置值
                            request.session.set_expiry(14 * 24 * 60 * 60)  # 2周内免登陆
                            print("设置了一小时免登陆")
                            # jaquer 会自动访问页面
                    else:
                        ret['status'] = False
                        ret['error'] = "密码错误请重新输入"
                else:
                    ret['status'] = False
                    ret['error'] = "该账号已冻结请联系系主任"
            else:
                ret['status'] = False
                ret['error'] = "学号不存在"
        except Exception as e:
            ret['status'] = False
            ret['error'] = '未知错误'
        return HttpResponse(json.dumps(ret))
    else:
        return HttpResponse("该页面还在准备中@@")


def home(request):
    if request.method == "GET":
        # session中获取值
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '0':
            # 登录成功后的操作
            user_code = request.session['user_code']  # 用户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  # 查找用户相关信息
            return render(request, 'StuHome.html', {'user_name': obj.user_name})
        else:
            return render(request, 'login.html')
    else:
        return HttpResponse("该页面还在准备中@@")


def select(request):
    if request.method == "GET":
        user_code = request.session['user_code']  # 用户账号
        obj = models.UserTable.objects.filter(user_code=user_code).first()  # 查找用户相关信息
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '0':
            return render(request, 'StuSelect.html', {'user_name': obj.user_name})
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取学生的账号
        login_dpartment_name_id = models.UserTable.objects.filter(
            user_code=login_user_code).first().dpartment_name_id  # 获取学生所属的系号
        return_data = {'status': True, 'data': None}  # 返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作
        if operate == "search":
            select_postil_flag = request.POST.get('select_postil_flag', None)  # 选择类型 0未审核 1已通过 2未通过 3全部
            dic_user_list = []  # 找到数据后返回的列表
            obj = []
            if select_postil_flag == "3":
                obj = models.SelectSubTable.objects.filter(stu_no=login_user_code,
                                                           dpartment_name_id=login_dpartment_name_id)
            else:
                obj = models.SelectSubTable.objects.filter(stu_no=login_user_code, postil_flag=select_postil_flag,
                                                           dpartment_name_id=login_dpartment_name_id)

            if len(obj) == 0:
                return_data['status'] = False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)  # 对象数据转字典       ###增加论文题目  和姓名
                    user_name = models.UserTable.objects.filter(user_code=jsonstr['stu_no']).first().user_name
                    jsonstr['user_name'] = user_name  # 在字典里增加 學生的名字
                    sub_name = models.SubjectTable.objects.filter(id=jsonstr['sub_no']).first().sub_name
                    jsonstr['sub_name'] = sub_name  # 在字典里增加 論文的題目
                    dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate == "add":
            add_sub_name = request.POST.get('add_sub_name', None)  # 论文题目
            add_year = request.POST.get('add_year', None)  # 参与年级
            add_wish_flag = request.POST.get('add_wish_flag', None)  # 选题志愿 1 2 3 4
            add_wish = request.POST.get('add_wish', None)  # 选题理由
            if add_year == "":
                return_data['status'] = False
                return_data['data'] = "年级不能为空"
                return JsonResponse(return_data, safe=False)
            if add_sub_name == "":
                return_data['status'] = False
                return_data['data'] = "论文题目不能不空"
                return JsonResponse(return_data, safe=False)
            elif len(models.SubjectTable.objects.filter(sub_name=add_sub_name, year=add_year)) == 0:
                return_data['status'] = False
                return_data['data'] = "论文题目不存在"
                return JsonResponse(return_data, safe=False)
            if add_wish == "":
                return_data['status'] = False
                return_data['data'] = "选择意愿不能为空"
                return JsonResponse(return_data, safe=False)

            ########## 1 2 3 4 志愿只能有一个 的判断       add_wish_flag
            if len(models.SelectSubTable.objects.filter(stu_no=login_user_code, wish_flag=add_wish_flag)) > 0:
                return_data['status'] = False
                return_data['data'] = "一种志愿意向只能选择一次"
                return JsonResponse(return_data, safe=False)

            # 判断人数上限
            sub_id = models.SubjectTable.objects.filter(sub_name=add_sub_name, year=add_year).first().id  # 获取论文题目的id号
            teacher_id = models.SubjectTable.objects.filter(sub_name=add_sub_name,
                                                            year=add_year).first().teacher_no  # 获取论文题目的老师的id
            max_part_in_no = models.SubjectTable.objects.filter(sub_name=add_sub_name,
                                                                year=add_year).first().part_in_no  # 获取论文最大参与人数上限

            if len(models.SelectSubTable.objects.filter(sub_no=sub_id, postil_flag="1", year=add_year)) >= int(
                    max_part_in_no):  # 如果超过最大选择人数
                return_data['status'] = False
                return_data['data'] = "论文参与人数已达上限"
                return JsonResponse(return_data, safe=False)
            # 增加选题意愿
            models.SelectSubTable.objects.create(teacher_no=teacher_id,
                                                 sub_no=sub_id,
                                                 stu_no=login_user_code,
                                                 dpartment_name_id=login_dpartment_name_id,
                                                 postil_flag='0',
                                                 year=add_year,
                                                 wish_flag=add_wish_flag,
                                                 wish=add_wish,
                                                 op_no=login_user_code)
            dic_user_list = []  # 找到数据后返回的列表
            obj = models.SelectSubTable.objects.filter(stu_no=login_user_code,
                                                       dpartment_name_id=login_dpartment_name_id)
            if len(obj) == 0:
                return_data['status'] = False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)  # 对象数据转字典       ###增加论文题目  和姓名
                    user_name = models.UserTable.objects.filter(user_code=jsonstr['stu_no']).first().user_name
                    jsonstr['user_name'] = user_name  # 在字典里增加 學生的名字
                    sub_name = models.SubjectTable.objects.filter(id=jsonstr['sub_no']).first().sub_name
                    jsonstr['sub_name'] = sub_name  # 在字典里增加 論文的題目
                    dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate == "change":
            change_select_id = request.POST.get('change_select_id', None)  # 获取操作的id
            change_sub_name = request.POST.get('change_sub_name', None)  # 论文题目
            change_year = request.POST.get('change_year', None)  # 年级
            change_wish_flag = request.POST.get('change_wish_flag', None)  # 志愿意向
            change_wish = request.POST.get('change_wish', None)  # 意愿理由
            if change_year == "":
                return_data['status'] = False
                return_data['data'] = "年级不能为空"
                return JsonResponse(return_data, safe=False)
            if change_sub_name == "":
                return_data['status'] = False
                return_data['data'] = "论文题目不能不空"
                return JsonResponse(return_data, safe=False)
            elif len(models.SubjectTable.objects.filter(sub_name=change_sub_name, year=change_year)) == 0:
                return_data['status'] = False
                return_data['data'] = "论文题目不存在"
                return JsonResponse(return_data, safe=False)
            if change_wish == "":
                return_data['status'] = False
                return_data['data'] = "选择意愿不能为空"
                return JsonResponse(return_data, safe=False)

            ########## 1 2 3 4 志愿只能有一个 的判断       change_wish_flag
            if len(models.SelectSubTable.objects.filter(stu_no=login_user_code, wish_flag=change_wish_flag)) > 0:
                if models.SelectSubTable.objects.filter(stu_no=login_user_code,
                                                        wish_flag=change_wish_flag).first().id != change_select_id:
                    return_data['status'] = False
                    return_data['data'] = "一种志愿意向只能选择一次"
                    return JsonResponse(return_data, safe=False)

            # 判断人数上限
            sub_id = models.SubjectTable.objects.filter(sub_name=change_sub_name,
                                                        year=change_year).first().id  # 获取论文题目的id号
            teacher_id = models.SubjectTable.objects.filter(sub_name=change_sub_name,
                                                            year=change_year).first().teacher_no  # 获取论文题目的老师的id
            max_part_in_no = models.SubjectTable.objects.filter(sub_name=change_sub_name,
                                                                year=change_year).first().part_in_no  # 获取论文最大参与人数上限

            if len(models.SelectSubTable.objects.filter(sub_no=sub_id, postil_flag="1", year=change_year)) >= int(
                    max_part_in_no):  # 如果超过最大选择人数
                return_data['status'] = False
                return_data['data'] = "论文参与人数已达上限"
                return JsonResponse(return_data, safe=False)

            # 修改选题意愿
            models.SelectSubTable.objects.filter(id=change_select_id).update(teacher_no=teacher_id,
                                                                             sub_no=sub_id,
                                                                             year=change_year,
                                                                             wish_flag=change_wish_flag,
                                                                             wish=change_wish,
                                                                             op_no=login_user_code)
            dic_user_list = []  # 找到数据后返回的列表
            obj = models.SelectSubTable.objects.filter(stu_no=login_user_code,
                                                       dpartment_name_id=login_dpartment_name_id)
            if len(obj) == 0:
                return_data['status'] = False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)  # 对象数据转字典       ###增加论文题目  和姓名
                    user_name = models.UserTable.objects.filter(user_code=jsonstr['stu_no']).first().user_name
                    jsonstr['user_name'] = user_name  # 在字典里增加 學生的名字
                    sub_name = models.SubjectTable.objects.filter(id=jsonstr['sub_no']).first().sub_name
                    jsonstr['sub_name'] = sub_name  # 在字典里增加 論文的題目
                    dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)

        # 删除时直接删掉 当前的用户
        elif operate == "delete":
            delete_select_id = request.POST.get('delete_select_id', None)  # 获取删除的选择号
            # 判断此同学未通过的个数   如果满足四个则  四个全部删除删除

            if len(models.SelectSubTable.objects.filter(stu_no=login_user_code, postil_flag="2",
                                                        dpartment_name_id=login_dpartment_name_id)) == 4:
                models.SelectSubTable.objects.filter(stu_no=login_user_code, postil_flag="2",
                                                     dpartment_name_id=login_dpartment_name_id).delete()  # 四个一起删除
                return JsonResponse(return_data, safe=False)
            else:
                return_data['status'] = False
                return_data['data'] = "四个志愿全部未通过才能重选"
                return JsonResponse(return_data, safe=False)

        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")


def history(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '0':
            return render(request, 'StuHistory.html')
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取登录学生的账号
        login_dpartment_name_id = models.UserTable.objects.filter(
            user_code=login_user_code).first().dpartment_name_id  # 获取当前的系号
        return_data = {'status': True, 'data': None}  # 返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作
        if operate == "search":
            find_user_name = request.POST.get('find_user_name', None)  # 用户名
            find_year = request.POST.get('find_year', None)  # 查找年级
            dic_user_list = []  # 找到数据后返回的列表
            obj = []
            if find_user_name == "":
                if find_year == "":
                    obj = models.SubjectTable.objects.filter(postil_flag="1", dpartment_name_id=login_dpartment_name_id)
                else:
                    obj = models.SubjectTable.objects.filter(year=find_year, postil_flag="1",
                                                             dpartment_name_id=login_dpartment_name_id)
            else:
                if len(models.UserTable.objects.filter(user_name=find_user_name)) > 0:  # 检查导师是否存在
                    user_code = models.UserTable.objects.filter(
                        user_name=find_user_name).first().user_code  # 获取老师名字 从数据库转换成用户ID
                    # 根据老师的姓名
                    if find_year == "":
                        obj = models.SubjectTable.objects.filter(teacher_no=user_code, postil_flag="1",
                                                                 dpartment_name_id=login_dpartment_name_id)
                    else:
                        obj = models.SubjectTable.objects.filter(teacher_no=user_code, year=find_year, postil_flag="1",
                                                                 dpartment_name_id=login_dpartment_name_id)
            if len(obj) == 0:
                return_data['status'] = False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)  # 对象数据转字典
                    user_name = models.UserTable.objects.filter(user_code=jsonstr['teacher_no']).first().user_name
                    jsonstr['user_name'] = user_name  # 在字典里增加 老师的名字
                    jsonstr['check_wish'] = len(
                        models.SelectSubTable.objects.filter(sub_no=line.id, postil_flag="1"))  # 通过审核的人数
                    jsonstr['wish_flag1'] = len(
                        models.SelectSubTable.objects.filter(sub_no=line.id, wish_flag='1'))  # 找到该题目 选择为第一志愿的人数
                    jsonstr['wish_flag2'] = len(
                        models.SelectSubTable.objects.filter(sub_no=line.id, wish_flag='2'))  # 找到该题目 选择为第二志愿的人数
                    jsonstr['wish_flag3'] = len(
                        models.SelectSubTable.objects.filter(sub_no=line.id, wish_flag='3'))  # 找到该题目 选择为第三志愿的人数
                    jsonstr['wish_flag4'] = len(
                        models.SelectSubTable.objects.filter(sub_no=line.id, wish_flag='4'))  # 找到该题目 选择为第四志愿的人数
                    dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")


def person(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '0':
            # 登录成功后的操作
            user_code = request.session['user_code']  # 获取操操作户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  # 查找用户相关信息
            return_dic = {'user_code': obj.user_code,
                          'user_name': obj.user_name,
                          'dpartment_name': obj.dpartment_name.dpartement_name,
                          'user_mail': obj.user_mail,
                          'user_phone': obj.user_phone,
                          'remark': obj.remark
                          }
            return_dic['user_mail'] = '无' if obj.user_mail is None else obj.user_mail
            return_dic['user_phone'] = '无' if obj.user_phone is None else obj.user_phone
            return_dic['remark'] = '无' if obj.remark is None else obj.remark
            return render(request, 'StuPerson.html', return_dic)
        else:
            return render(request, 'login.html')
    elif request.method == "POST":
        ret = {'status': True, 'error': None}
        user_code = request.session['user_code']  # 获取操作用户账号
        obj = models.UserTable.objects.filter(user_code=user_code).first()
        up_data_dic = {'user_name': obj.user_name,
                       'user_password': obj.user_password,
                       'user_mail': obj.user_mail,
                       'user_phone': obj.user_phone,
                       "op_no": user_code
                       }
        user_name = request.POST.get('user_name', None)  # 沒有则为空
        old_password = request.POST.get('old_password', None)
        new_password = request.POST.get('new_password', None)
        again_password = request.POST.get('again_password', None)
        user_phone = request.POST.get('user_phone', None)
        user_mail = request.POST.get('user_mail', None)
        change_password = request.POST.get('change_password', None)

        if len(user_name) == 0:
            ret['status'] = False
            ret['error'] = '姓名不能为空'
            return HttpResponse(json.dumps(ret))
        up_data_dic["user_name"] = user_name

        if change_password == "true":
            if old_password == obj.user_password:
                if new_password != again_password:
                    ret['status'] = False
                    ret['error'] = '两次密码输入不一致'
                    return HttpResponse(json.dumps(ret))
            else:
                ret['status'] = False
                ret['error'] = '原始密码错误'
                return HttpResponse(json.dumps(ret))
            up_data_dic["user_password"] = new_password

        if user_phone == "无" or user_phone == "":
            up_data_dic["user_phone"] = None
        else:
            up_data_dic["user_phone"] = user_phone
        if user_mail == "无" or user_mail == "":
            up_data_dic["user_mail"] = None
        else:
            up_data_dic["user_mail"] = user_mail

        models.UserTable.objects.filter(user_code=user_code).update(user_name=up_data_dic["user_name"],
                                                                    user_mail=up_data_dic["user_mail"],
                                                                    user_phone=up_data_dic["user_phone"],
                                                                    user_password=up_data_dic["user_password"],
                                                                    op_no=up_data_dic["op_no"])
        return HttpResponse(json.dumps(ret))


def logout(request):
    # del request.session['user_code']
    request.session.clear()
    return redirect('/login/')
