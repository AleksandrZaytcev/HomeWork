## Домашняя работа №2

1. Добавить новый opcode в Python (см. детали ниже)
2. Добавить until в Python
* http://eli.thegreenplace.net/2010/06/30/python-internals-adding-a-new-statement-to-python/
3. [опционально] Добавить инткремент и декремент
https://hackernoon.com/modifying-the-python-language-in-7-minutes-b94b0a99ce14
для самых смелых и сильных духом
### **Ограничения:**
* cpython 2.7
* centos 7
   * рекомендую docker, см. code sample ниже

**В результате выполнения кажого задания получается:**
1. бинарь python
2. git diff > my.patch
   * имя патча в зависимости от задания: new_opcode.patch, unitl.patch, inc.patch