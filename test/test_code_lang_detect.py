
import os, sys 
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
sys.path.insert(0, parentdir)

import tools
from pyshould import should
import pytest


from tools import guess_lang_pygments, guess_lang, trim_leading_spaces




mds = ['''
    1、分析 Diff 源码比较步骤

    2、个人思考为什么如此比较

    3、写个例子，一步步走个Diff 流程
''',

'''
    1、没有旧节点

    2、旧节点 和 新节点 自身一样（不包括其子节点）

    3、旧节点 和 新节点自身不一样

''',

'''
###  **re模块**

1. 在正则表达式中，增加对spans修饰符的支持。示例: '(?i:p)ython' 匹配 'python' 和 'Python', 但不匹配 'PYTHON'； '(?i)g(?-i:v)r' 匹配 'GvR' 和 'gvr', 但不匹配 'GVR'。
2. 匹配对象组可通过__getitem__访问, 它就等价于 group()。因此， 现在mo['name'] 就等价于 mo.group('name')。
3. Match对象支持index-like对象一样的组索引。

''',

'''
![](https://pic3.zhimg.com/v2-1458319c3f94c67ed9d11177487254dd_b.jpg)

刚才看到[Learn Python the Hard Way](https://learnpythonthehardway.org/python3/)第四版都开始使用Python 3.6?，。
想起当时某些人还吐槽我的书竟然是使用Python 2的，好吧，我也来列一下Python 3.6中非常值得一提的变化
（最详细的当然还是看官方的[What’s New](https://docs.python.org/3.6/whatsnew/3.6.html)）。

''',


]

javascripts =  ['''
    var patch = createPatchFunction();

    Vue.prototype.__patch__ =  patch
''',

'''
    function createPatchFunction() {

        return function patch(

            oldVnode, vnode, parentElm, refElm

        ) {

            // 没有旧节点，直接生成新节点

            if (!oldVnode) {
                createElm(vnode, parentElm, refElm);
            }
            else {
                // 且是一样 Vnode

                if (sameVnode(oldVnode, vnode)) {

                    // 比较存在的根节点

                    patchVnode(oldVnode, vnode);
                }
                else {

                    // 替换存在的元素

                    var oldElm = oldVnode.elm;

                    var _parentElm = oldElm.parentNode

                    // 创建新节点

                    createElm(vnode, _parentElm, oldElm.nextSibling);

                    // 销毁旧节点

                    if (_parentElm) {
                        removeVnodes([oldVnode], 0, 0);
                    }
                }
            }

            return vnode.elm

        }
    }

''',

'''
    function patchVnode(oldVnode, vnode) {

        if (oldVnode === vnode) return

        var elm = vnode.elm = oldVnode.elm;

        var oldCh = oldVnode.children;

        var ch = vnode.children;

        // 更新children

        if (!vnode.text) {

            // 存在 oldCh 和 ch 时

            if (oldCh && ch) {

                if (oldCh !== ch)

                    updateChildren(elm, oldCh, ch);

            }

            // 存在 newCh 时，oldCh 只能是不存在，如果存在，就跳到上面的条件了

            else if (ch) {

                if (oldVnode.text) elm.textContent = '';

                for (var i = 0; i <= ch.length - 1; ++i) {

                    createElm(
                      ch[i],elm, null
                    );
                }

            }

            else if (oldCh) {

                for (var i = 0; i<= oldCh.length - 1; ++i) {

                    oldCh[i].parentNode.removeChild(el);
                }

            }

            else if (oldVnode.text) {
                elm.textContent = '';
            }
        }

        else if (oldVnode.text !== vnode.text) {
            elm.textContent = vnode.text;
        }
    }
''',

'''
    elm.textContent = vnode.text;
''',

'''
    function updateChildren(parentElm, oldCh, newCh) {

        var oldStartIdx = 0;

        var oldEndIdx = oldCh.length - 1;

        var oldStartVnode = oldCh[0];

        var oldEndVnode = oldCh[oldEndIdx];

        var newStartIdx = 0;

        var newEndIdx = newCh.length - 1;

        var newStartVnode = newCh[0];

        var newEndVnode = newCh[newEndIdx];

        var oldKeyToIdx, idxInOld, vnodeToMove, refElm;


        // 不断地更新 OldIndex 和 OldVnode ，newIndex 和 newVnode

        while (

            oldStartIdx <= oldEndIdx &&

            newStartIdx <= newEndIdx

        ) {

            if (!oldStartVnode) {

                oldStartVnode = oldCh[++oldStartIdx];
            }

            else if (!oldEndVnode) {

                oldEndVnode = oldCh[--oldEndIdx];
            }

            //  旧头 和新头 比较
            else if (sameVnode(oldStartVnode, newStartVnode)) {

                patchVnode(oldStartVnode, newStartVnode);

                oldStartVnode = oldCh[++oldStartIdx];
                newStartVnode = newCh[++newStartIdx];
            }

            //  旧尾 和新尾 比较

            else if (sameVnode(oldEndVnode, newEndVnode)) {

                patchVnode(oldEndVnode, newEndVnode);

                oldEndVnode = oldCh[--oldEndIdx];
                newEndVnode = newCh[--newEndIdx];
            }


            // 旧头 和 新尾 比较

            else if (sameVnode(oldStartVnode, newEndVnode)) {

                patchVnode(oldStartVnode, newEndVnode);

                // oldStartVnode 放到 oldEndVnode 后面，还要找到 oldEndValue 后面的节点

                parentElm.insertBefore(

                    oldStartVnode.elm,

                    oldEndVnode.elm.nextSibling

                );

                oldStartVnode = oldCh[++oldStartIdx];
                newEndVnode = newCh[--newEndIdx];
            }

            //  旧尾 和新头 比较

            else if (sameVnode(oldEndVnode, newStartVnode)) {

                patchVnode(oldEndVnode, newStartVnode);


                // oldEndVnode 放到 oldStartVnode 前面

                parentElm.insertBefore(oldEndVnode.elm, oldStartVnode.elm);

                oldEndVnode = oldCh[--oldEndIdx];
                newStartVnode = newCh[++newStartIdx];
            }


            // 单个新子节点 在 旧子节点数组中 查找位置

            else {

                // oldKeyToIdx 是一个 把 Vnode 的 key 和 index 转换的 map

                if (!oldKeyToIdx) {
                    oldKeyToIdx = createKeyToOldIdx(

                        oldCh, oldStartIdx, oldEndIdx

                    );

                }

                // 使用 newStartVnode 去 OldMap 中寻找 相同节点，默认key存在

                idxInOld = oldKeyToIdx[newStartVnode.key]

                //  新孩子中，存在一个新节点，老节点中没有，需要新建

                if (!idxInOld) {

                    //  把  newStartVnode 插入 oldStartVnode 的前面

                    createElm(

                        newStartVnode,

                        parentElm,

                        oldStartVnode.elm

                    );

                }

                else {

                    //  找到 oldCh 中 和 newStartVnode 一样的节点

                    vnodeToMove = oldCh[idxInOld];
                    if (sameVnode(vnodeToMove, newStartVnode)) {

                        patchVnode(vnodeToMove, newStartVnode);

                        // 删除这个 index

                        oldCh[idxInOld] = undefined;
                        // 把 vnodeToMove 移动到  oldStartVnode 前面

                        parentElm.insertBefore(

                            vnodeToMove.elm,

                            oldStartVnode.elm

                        );

                    }

                    // 只能创建一个新节点插入到 parentElm 的子节点中

                    else {

                        // same key but different element. treat as new element

                        createElm(

                            newStartVnode,

                            parentElm,

                            oldStartVnode.elm

                        );

                    }
                }

                // 这个新子节点更新完毕，更新 newStartIdx，开始比较下一个

                newStartVnode = newCh[++newStartIdx];
            }
        }


        // 处理剩下的节点

        if (oldStartIdx > oldEndIdx) {

            var newEnd = newCh[newEndIdx + 1]

            refElm = newEnd ? newEnd.elm :null;
            for (; newStartIdx <= newEndIdx; ++newStartIdx) {

                createElm(
                   newCh[newStartIdx], parentElm, refElm
                );
            }
        }

        // 说明新节点比对完了，老节点可能还有，需要删除剩余的老节点

        else if (newStartIdx > newEndIdx) {

            for (; oldStartIdx<=oldEndIdx; ++oldStartIdx) {

                oldCh[oldStartIdx].parentNode.removeChild(el);
            }
        }
    }
''',

'''
    parentElm.insertBefore(
        oldStartVnode.elm,
        oldEndVnode.elm.nextSibling
    );
''',

'''
    parentElm.insertBefore(
        oldEndVnode.elm,
        oldStartVnode.elm
    );
''',
]


pythons = [
'''
    #python2

    timeit.timeit('1000000000 in range(0,1000000000,10)', number=1)
    5.50357640805305

    timeit.timeit('1000000000 in xrange(0,1000000000,10)', number=1)
    2.3025200839183526

    # python3

    import timeit
    timeit.timeit('1000000000 in range(0,1000000000,10)', number=1)
    4.490355838248402e-06
''',

'''
    ❯ pip install "celery[librabbitmq,redis,msgpack]"
''',

'''
    from __future__ import absolute_import

    from celery import Celery

    app = Celery('proj', include=['proj.tasks'])

    app.config_from_object('proj.celeryconfig')


    if __name__ == '__main__':

        app.start()
''',

'''
    from __future__ import absolute_import

    from proj.celery import app


    @app.task

    def add(x, y):

        return x + y
''',

'''
    In : from proj.tasks import add

    In : r = add.delay(1, 3)

    In : r

    Out: <AsyncResult: 93288a00-94ee-4727-b815-53dc3474cf3f>

    In : r.result

    Out: 4

    In : r.status

    Out: u'SUCCESS'
    In : r.successful()

    Out: True

    In : r.backend

    Out: <celery.backends.redis.RedisBackend at 0x7fb2529500d0> # 保存在Redis中
''',

'''
    from kombu import Queue

    CELERY_QUEUES = ( # 定义任务队列

    Queue('default', routing_key='task.#'), # 路由键以“task.”开头的消息都进default队列

    Queue('web_tasks', routing_key='web.#'), # 路由键以“web.”开头的消息都进web_tasks队列

    )

    CELERY_DEFAULT_EXCHANGE = 'tasks' # 默认的交换机名字为tasks

    CELERY_DEFAULT_EXCHANGE_TYPE = 'topic' # 默认的交换类型是topic

    CELERY_DEFAULT_ROUTING_KEY = 'task.default' # 默认的路由键是task.default，这个路由键符合上面的default队列

    CELERY_ROUTES = {

        'projq.tasks.add': { # tasks.add的消息会进入web_tasks队列

        'queue': 'web_tasks',

        'routing_key': 'web.add',

        }

    }
''',

'''
    result = [await fun() for fun in funcs]
    result = {await fun() for fun in funcs}
    result = {fun: await fun() for fun in funcs}
    result = [func async for fun in funcs]
    result = {func async for fun in funcs}
    result = {func async for fun in funcs}
''',

'''
    >>> '{:_}'.format(1000000)
    '1_000_000'
    >>> 10_000_000.0
    10000000.0
''',

'''
    class Integer(object):
        def __init__(self, name):
            self.name = name

        def __get__(self, instance, owner):
           return instance.__dict__[self.name]

        def __set__(self, instance, value):
            if value < 0:
                raise ValueError('Negative value not allowed')
            instance.__dict__[self.name] = value


    class Movie(object):
        score = Integer('score')
        amount = Integer('amount')


    movie = Movie()
    movie.score = 9
    print(movie.score)
''',


]



def test_0a_if_trim_leading_spaces_works():
  r1 = [guess_lang(code) for code in mds]
  r2 = [guess_lang(code) for code in javascripts]
  r3 = [guess_lang(code) for code in pythons]
  r4 = [guess_lang(trim_leading_spaces(code)) for code in mds]
  r5 = [guess_lang(trim_leading_spaces(code)) for code in javascripts]
  r6 = [guess_lang(trim_leading_spaces(code)) for code in pythons]
  r1 + r2 + r3 | should.equal(r4 + r5 + r6) 
  # Expected: <['markdown', 'markdown', 'sql', 'markdown', 'go', 'javascript', 'javascript', 'javascript', 'objective-c', 'javascript', 'javascript', 'python', 'scala', 'python', 'python', 'ruby', 'python', 'markdown', 'scala', 'python']>
  #  r1+r2+r3 <['markdown', 'markdown', 'sql', 'markdown', 'go', 'markdown',   'javascript', 'javascript', 'markdown',    'javascript', 'javascript', 'python', 'scala', 'python', 'python', 'ruby', 'python', 'markdown', 'scala', 'python']>
  # 留有行首空格, 会增大误判为 md 的几率

def test_0b_if_trim_leading_spaces_works():
  r1 = [guess_lang_pygments(code) for code in mds]
  r2 = [guess_lang_pygments(code) for code in javascripts]
  r3 = [guess_lang_pygments(code) for code in pythons]
  r4 = [guess_lang_pygments(trim_leading_spaces(code)) for code in mds]
  r5 = [guess_lang_pygments(trim_leading_spaces(code)) for code in javascripts]
  r6 = [guess_lang_pygments(trim_leading_spaces(code)) for code in pythons]
  r1 + r2 + r3 | should.equal(r4 + r5 + r6) 
  # Expected: <['text', 'text', 'text', 'text', 'text', 'typescript', 'typescript', 'text', 'typescript', 'text', 'text', 'python', 'text', 'python', 'python', 'python', 'python', 'text', 'text', 'typescript']>
  # r1+r2+r3  <['text', 'text', 'text', 'text', 'text', 'text',       'text',       'text', 'text',       'text', 'text', 'python', 'text', 'python', 'python', 'python', 'python', 'text', 'text', 'perl6']>
  # guess_lang_pygments 效果不好, 再加上留有行首空格, 更差了



def test_1_detect_mds():
  result = ['markdown' for code in mds]
  [guess_lang(code) for code in mds]           | should.equal(result)

def test_2_detect_javascripts():
  result = ['javascript' for code in javascripts]
  [guess_lang(code) for code in javascripts]           | should.equal(result)

def test_3_detect_javascripts_trim_leading_spaces():
  result = ['javascript' for code in javascripts]
  [guess_lang(trim_leading_spaces(code)) for code in javascripts]           | should.equal(result)


def test_4_detect_pythons():
  result = ['python' for code in pythons]
  [guess_lang(code) for code in pythons]           | should.equal(result)


def test_5_detect_pythons_trim_leading_spaces():
  result = ['python' for code in pythons]
  [guess_lang(trim_leading_spaces(code)) for code in pythons]           | should.equal(result)




# 总结:
# guess_lang (with tersorflow) 加上除去行首空格, 效果最好, 但还是有误判