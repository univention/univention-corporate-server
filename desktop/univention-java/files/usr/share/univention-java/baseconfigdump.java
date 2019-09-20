/*
 * Univention Java
 *  source code for the java demonstration of UCR
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

import java.io.*;
import java.util.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

public class baseconfigdump
	implements WindowListener
{
	private final static String baseconfFilename 	= "/etc/univention/base.conf";
	private final static String productName		= "Univention Corporate Server";
	private final static String keyVersion 		= "version/repository-version";
	private final static String keyPatchlevel 	= "version/patchlevel";

	private JButton button = null;


	public baseconfigdump(String header, String sortedDump)
	{
		if (!GraphicsEnvironment.isHeadless()) {
			JTextArea textArea = new JTextArea(sortedDump);
			textArea.setEditable(false);
			textArea.setColumns(60);
			textArea.setRows(25);

			JFrame mainWin = new JFrame(header);
			mainWin.getContentPane().add(new JScrollPane(textArea));
			mainWin.pack();
			mainWin.show();
			mainWin.addWindowListener(this);
		}
		else {
			System.out.println(header);
			System.out.println(sortedDump);
		}
	}

	public void windowActivated(WindowEvent e) {}
	public void windowClosed(WindowEvent e) {}
	public void windowDeactivated(WindowEvent e) {}
	public void windowDeiconified(WindowEvent e) {}
	public void windowIconified(WindowEvent e) {}
	public void windowOpened(WindowEvent e) {}

	public void windowClosing(WindowEvent e)
	{
		System.exit(0);
	}

	private static Properties getBaseConfig(String filename)
		throws Exception
	{
		Properties returnValue = new Properties();

		try {
			FileInputStream stream = new FileInputStream(new File(filename));
			returnValue.load(stream);
		}
		catch (FileNotFoundException e) {
			throw new Exception("Could not open \"" + filename + "\"", e);
		}
		catch (IOException e) {
			throw new Exception("Error while reading \"" + filename + "\"", e);
		}

		return returnValue;
	}

	private static String getHeader(String product, String version, String patchlevel)
	{
		String returnValue = product + " (Version " + version;

		if ((patchlevel != null) && (!"".equals(patchlevel)))
			returnValue += "-" + patchlevel;
		returnValue += ")";

		return returnValue;
	}

	private static String getSortedDump(Properties props)
	{
		String returnValue = "";
		Vector allKeysVec = new Vector();

		Enumeration num = props.propertyNames();
		while (num.hasMoreElements())
			allKeysVec.add(num.nextElement());

		String[] allKeys = (String[])allKeysVec.toArray(new String[0]);
		Arrays.sort(allKeys);

		for (int i=0; i<allKeys.length; i++)
			returnValue += allKeys[i] + ": " + props.getProperty(allKeys[i]) + "\n";

		return returnValue;
	}

	public static void main(String[] args)
		throws Exception
	{
		Properties baseconfig	= getBaseConfig(baseconfFilename);
		String version		= baseconfig.getProperty(keyVersion);
		String patchlevel	= baseconfig.getProperty(keyPatchlevel);

		String header = getHeader(productName, version, patchlevel);
		String sortedDump = getSortedDump(baseconfig);

		try {
			baseconfigdump app = new baseconfigdump(header, sortedDump);
		}
		catch (java.lang.InternalError e) {
			System.out.println("  Failed to start due to an Error, reason was: ");
			System.out.println("  "+e.getMessage());
		}
	}
}
