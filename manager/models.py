# 管理员的APP中
from django.db import models


# 创建数据表
# 表名  manage_usertable

# 建立系表  系表
class DpartmentTable(models.Model):
    # 默认自动创建主键id
    dpartement_name = models.CharField(max_length=20, null=True)  # 系名称
    op_time = models.DateTimeField(auto_now_add=True)  # 创建时 更新为当前时间


# 创建  系统用户信息表
class UserTable(models.Model):
    # 默认自动创建主键ID
    user_code = models.CharField(max_length=20)  # 账号 默认不为空
    user_password = models.CharField(max_length=20)  # 密码
    dpartment_name = models.ForeignKey("DpartmentTable", to_field='id', on_delete=models.CASCADE, null=True)  # 外键  系名
    user_name = models.CharField(max_length=10)  # 用户的名字
    user_mail = models.CharField(max_length=100, null=True)  # 邮箱可以为空
    user_phone = models.CharField(max_length=20, null=True)  # 电话号码
    user_stat = models.CharField(max_length=1)  # 用户状态   1 正常用户 2冻结用户
    user_type = models.CharField(max_length=1)  # 用户类型  0 学生 1 导师 2 系主任 3 超级管理员
    stu_num = models.CharField(max_length=2, null=True)  # 导师指导学生上限
    remark = models.CharField(max_length=500, null=True)  # 备注
    op_no = models.CharField(max_length=20)  # 操作人员编号
    op_time = models.DateTimeField(auto_now_add=True)  # 创建时 更新为当前时间


# 论文出题表
class SubjectTable(models.Model):
    # 默认自动创建主键ID  即是题目编号
    sub_name = models.CharField(max_length=100)  # 论文题目名称
    teacher_no = models.CharField(max_length=20)  # 出题教师编号
    dpartment_name = models.ForeignKey("DpartmentTable", to_field='id', on_delete=models.CASCADE)  # 外键  题目所属的系名
    part_in_no = models.CharField(max_length=10)  # 参与人数上限
    sub_viscera = models.CharField(max_length=1000)  # 题目内容
    postil_flag = models.CharField(max_length=1, null=True)  # 主任审核标识  0 未审核 1 审核通过 2 审核未通过
    postil = models.CharField(max_length=200, null=True)  # 主任审核意见
    year = models.CharField(max_length=4)  # 年级
    op_no = models.CharField(max_length=20)  # 操作人员编号
    op_time = models.DateTimeField(auto_now_add=True)  # 创建时 更新为当前时间


# 论文选题表
class SelectSubTable(models.Model):
    # 默认自动创建主键ID
    teacher_no = models.CharField(max_length=20)  # 出题教师编号  即是用户的账号
    sub_no = models.CharField(max_length=20)  # 论文题目编号
    stu_no = models.CharField(max_length=20)  # 学生编号
    dpartment_name = models.ForeignKey("DpartmentTable", to_field='id', on_delete=models.CASCADE)  # 外键 系名
    postil_flag = models.CharField(max_length=1, null=True)  # 教师审核标识  0 未审核 1 审核通过 2 审核未通过
    postil = models.CharField(max_length=200, null=True)  # 教师审核意见
    year = models.CharField(max_length=4)  # 年级
    wish_flag = models.CharField(max_length=1)  # 志愿标识  1 第一志愿 2 第二志愿 3 第三志愿  4 其他志愿
    wish = models.CharField(max_length=200, null=True)  # 选择理由
    op_no = models.CharField(max_length=20)  # 操作人员编号
    op_time = models.DateTimeField(auto_now_add=True)  # 创建时 更新为当前时间
