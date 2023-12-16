import { Fragment, useState, useMemo } from 'react';
import { JsonForms } from '@jsonforms/react';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import './App.css';
import schema from './schema.json';
import uischema from './uischema.json';
import {
  materialCells,
  materialRenderers,
} from '@jsonforms/material-renderers';
import { makeStyles } from '@mui/styles';

import initialData from './defaultactions.json';


const useStyles = makeStyles({
  container: {
    padding: '1em',
    width: '100%',
  },
  title: {
    textAlign: 'center',
    padding: '0.25em',
  },
  dataContent: {
    display: 'flex',
    justifyContent: 'left',
    borderRadius: '0.25em',
    backgroundColor: '#cecece',
    marginBottom: '1rem',
  },
  resetButton: {
    margin: 'auto !important',
    display: 'block !important',
    justifyContent: 'center',
  },
  demoform: {
    margin: 'auto',
    padding: '1rem',
  },
});

const renderers = [
  ...materialRenderers,
  //register custom renderers
];

const App = () => {
  const classes = useStyles();
  const [data, setData] = useState<any>(initialData);
  const stringifiedData = useMemo(() => JSON.stringify(data, null, 2), [data]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const input = event.target;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        const fileContent = e.target?.result as string;
        if (fileContent) {
          setData(JSON.parse(fileContent as string));
        }
      };
      reader.readAsText(file);
    }
  };

  const clearData = () => {
      setData(initialData);
  };

  const downloadFile = () => {
    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'iofile.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Fragment>

      <Grid
        container
        justifyContent={'center'}
        spacing={1}
        className={classes.container}
      >

        <Grid item sm={7}>
          <div className={classes.demoform}>
            <JsonForms
              schema={schema}
              uischema={uischema}
              data={data}
              renderers={renderers}
              cells={materialCells}
              onChange={({ errors, data }) => setData(data)}
            />
          </div>
        </Grid>

        <Grid item sm={5}>
            <input
            type='file'
            accept='.json'
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            id='fileInput'
            />
            <label htmlFor='fileInput'>
              <Button
                className={classes.resetButton}
                component='span'
                color='primary'
                variant='contained'
                >
                Upload File
              </Button>
            </label>

          <Button
            className={classes.resetButton}
            component='span'
            onClick={downloadFile}
            color='primary'
            variant='contained'
            >
            Download File
          </Button>

          <Button
            className={classes.resetButton}
            component='span'
            onClick={clearData}
            color='primary'
            variant='contained'
            >
           Clear All
          </Button>

          <div className={classes.dataContent}>
            <pre id='boundData'>{stringifiedData}</pre>
          </div>
        </Grid>
      </Grid>
    </Fragment>
  );
};

export default App;
