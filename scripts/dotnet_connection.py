# This source file is part of Spadecs.
# Spadecs is available through the world-wide-web at this URL:
#   https://github.com/Conticop/Spadecs
#
# This source file is subject to the MIT license.
#
# Copyright (c) 2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import dotnet_const
from dotnet_const import CONNECTION, CONFIG

if dotnet_const.CLR_LIB:
    import dotnet_exports


class DotNetConnection(CONNECTION):
    def __init__(self, *args, **kwargs):
        CONNECTION.__init__(self, *args, **kwargs)
        dotnet_const.CONNECTION_OBJ = self
        # self.OnConnectCallback = (FalseLogic, TrueLogic, PassLogic)
        # print("[dotnet] Connection initialized")

    def on_connect(self, *args, **kwargs):
        ipAddress = self.address[0].encode("utf-8")
        # print("pre_player_connect", type(ipAddress), ipAddress)
        result = dotnet_exports.dotnet_event_pre_player_connect(ipAddress)
        # self.OnConnectCallback[result]()
        if result == 0:
            return False
        if result == 1:
            return True
        result = CONNECTION.on_connect(self, *args, **kwargs)
        pid = self.player_id
        # print("post_player_connect", type(pid), pid)
        post_result = dotnet_exports.dotnet_event_post_player_connect(ipAddress, pid)
        return (False, True, result)[post_result]
