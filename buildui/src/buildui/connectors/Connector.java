package buildui.connectors;
/*
 * Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
 * This file is part of ToMaTo (Topology management software)
 *
 * Emulab is free software, also known as "open source;" you can
 * redistribute it and/or modify it under the terms of the GNU Affero
 * General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * Emulab is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
 * more details, which can be found in the file AGPL-COPYING at the root of
 * the source tree.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import buildui.devices.Device;
import buildui.paint.IconElement;
import java.util.HashSet;
import java.util.Set;
import org.w3c.dom.Element;

public abstract class Connector extends IconElement {

  public static Connector readFrom (Element x_con) {
    String type = x_con.getAttribute("type");
    if ( type.equals("real") ) return InternetConnector.readFrom(x_con);
    if ( type.equals("hub") ) return HubConnector.readFrom(x_con);
    if ( type.equals("switch") ) return SwitchConnector.readFrom(x_con);
    if ( type.equals("router") ) return RouterConnector.readFrom(x_con);
    return null;
  }

  public static void init () {
    nextSubnetId = 1;
  }

  public Connector (String newName, String iconName) {
    super(newName, true, iconName);
  }

  public abstract Connection createConnection ( Device dev ) ;
  protected static int nextSubnetId = 1;

  private Set<Connection> connections = new HashSet<Connection> () ;
  protected int subnetId;

  protected int nextHostIp = 1 ;

  public Set<Connection> connections() {
    return connections ;
  }

  public void addConnection(Connection con) {
    connections.add(con);
  }

  public void removeConnection(Connection con) {
    connections.remove(con);
  }

  public void writeAttributes(Element xml) {
    xml.setAttribute("id", getName());
    xml.setAttribute("pos", getX()+","+getY()) ;
  }

  public void readAttributes (Element xml) {
    String pos = xml.getAttribute("pos");
    try {
      int x = Integer.parseInt(pos.split(",")[0]);
      int y = Integer.parseInt(pos.split(",")[1]);
      move(x,y);
    } catch ( NumberFormatException ex ) {}
  }
}
