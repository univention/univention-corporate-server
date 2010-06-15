function openColorPicker(target)
{
    var lay = document.getElementById('colorpicker_' + target);
    if (lay.style.display == 'block') {
        lay.style.display = 'none';
        return false;
    }

    if (lay.firstChild) {
        if (lay.firstChild.nodeType == 1) {
            lay.style.display = 'block';
            return false;
        }
        else {
            lay.removeChild(lay.firstChild);
        }
    }

    var table = document.createElement('table');
    var tbody = document.createElement('tbody');
    table.appendChild(tbody);
    table.cellSpacing = 0;
    table.border = 0;
    table.style.cursor = 'crosshair';
    table.onmouseout = function() {
        document.getElementById('colordemo_' + target).style.backgroundColor = document.getElementById(target).value;
        return false;
    }

    // The palette
    r = 0; g = 0; b = 0;
    for (b = 0; b < 6; b++) {
        row = document.createElement('tr');
        color = makeColor(b * 51, b * 51, b * 51);
        cell = makeCell(target, color);
        row.appendChild(cell);
        for (g = 0; g < 6; g++) {
            for (r = 0; r < 6; r++) {
                if (r != b && b != g) {
                    color = makeColor(r * 51, g * 51, b * 51);
                    cell = makeCell(target, color);
                    row.appendChild(cell);
                }
            }
        }
        tbody.appendChild(row);
    }

    table.appendChild(tbody);
    lay.appendChild(table);
    lay.style.display = 'block';
}

function makeCell(target, color)
{
    cell = document.createElement('td');
    cell.height = 3;
    cell.width = 6;
    cell.id = color;
    cell.style.backgroundColor = color;
    cell.onmouseover = function() {
        document.getElementById('colordemo_' + target).style.backgroundColor = this.style.backgroundColor;
        return false;
    }
    cell.onclick = function() {
        document.getElementById('colordemo_' + target).style.backgroundColor = this.style.backgroundColor;
        document.getElementById(target).value = this.id;
        return false;
    }

    return cell;
}

function makeColor(r, g, b)
{
    color = "#";
    color += hex(Math.floor(r / 16));
    color += hex(r % 16);
    color += hex(Math.floor(g / 16));
    color += hex(g % 16);
    color += hex(Math.floor(b / 16));
    color += hex(b % 16);
    return color;
}

function hex(Dec)
{
    if (Dec == 10) return "a";
    if (Dec == 11) return "b";
    if (Dec == 12) return "c";
    if (Dec == 13) return "d";
    if (Dec == 14) return "e";
    if (Dec == 15) return "f";
    return "" + Dec;
}
