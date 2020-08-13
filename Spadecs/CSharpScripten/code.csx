class LogConnection : IConnection {
    public bool? OnPrePlayerConnect(in IPAddress ipAddress) {
        Console.WriteLine("[Pre] Player connecting: {0}", ipAddress);
        return true;
    }

    public void OnPostPlayerConnect(ref bool overrideAccess, in IPAddress ipAddress, in byte playerID) {
        Console.WriteLine("[Post] Player connecting ({0}): #{1} from {2}", overrideAccess, playerID, ipAddress);
    }
}

return (null, new LogConnection());