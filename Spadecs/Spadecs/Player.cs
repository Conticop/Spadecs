// This source file is part of Spadecs.
// Spadecs is available through the world-wide-web at this URL:
//   https://github.com/Conticop/Spadecs
//
// This source file is subject to the MIT license.
//
// Copyright (c) 2020
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

using System.Net;
using System.Numerics;

namespace Spadecs
{
    using static PyBindings;

    public interface IPlayer
    {
        public IPAddress Address { get; init; }

        public string Name { get; init; }

        public Vector3 Position { get; set; }

        public Vector3 Rotation { get; set; }

        public int Health { get; set; }

        public ETeam Team { get; set; }

        public byte ID { get; init; }

        public void Kick();
    }

    public unsafe class Player : IPlayer
    {
        public IPAddress Address { get; init; }

        public string Name { get; init; }

        public Vector3 Position { get; set; }

        public Vector3 Rotation { get; set; }

        public int Health { get; set; }

        public ETeam Team { get; set; }

        public byte ID { get; init; }

        public void Kick() => CPlayer_KickByID(ID);
    }

    public abstract class BaseWeapon
    {
        protected internal BaseWeapon(EWeapon id, string name, double delay, int ammo, int stock, double reloadTime, bool slowReload, IWeaponDamage damage)
        {
            ID = id;
            Name = name;
            Delay = delay;
            Ammo = ammo;
            Stock = stock;
            ReloadTime = reloadTime;
            SlowReload = slowReload;
            Damage = damage;
        }

        public EWeapon ID { get; }

        public string Name { get; }

        public double Delay { get; }

        public int Ammo { get; }

        public int Stock { get; }

        public double ReloadTime { get; }

        public bool SlowReload { get; }

        public IWeaponDamage Damage { get; }

        public bool Shoot { get; set; }

        public bool Reloading { get; set; }

        public int CurrentAmmo { get; set; }

        public int CurrentStock { get; set; }

        public virtual int GetDamage(EBodyPart bodyPart, Vector3 position1, Vector3 position2)
        {
            return Damage[(int)bodyPart];
        }
    }

    public sealed class Rifle : BaseWeapon
    {
        public Rifle() : base(EWeapon.Rifle, "Rifle", 0.5, 10, 50, 2.5, false, new WeaponDamage(49, 100, 33, 33))
        {
        }
    }

    public sealed class SMG : BaseWeapon
    {
        public SMG() : base(EWeapon.SMG, "SMG", 0.11, 30, 120, 2.5, false, new WeaponDamage(29, 75, 18, 18))
        {
        }
    }

    public sealed class Shotgun : BaseWeapon
    {
        public Shotgun() : base(EWeapon.Shotgun, "Shotgun", 1.0, 6, 48, 0.5, true, new WeaponDamage(27, 37, 16, 16))
        {
        }
    }
}