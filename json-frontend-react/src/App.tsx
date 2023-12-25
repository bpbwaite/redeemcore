import { Fragment, useState, useEffect, useMemo } from 'react';
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

const useStyles = makeStyles({
	container: {
		padding: '1em',
		width: '100%',
	},
	title: {
		textAlign: 'center',
		padding: '0.2em',
	},
	dataContent: {
		display: 'flex',
		justifyContent: 'left',
		borderRadius: '0.25em',
		backgroundColor: '#cecece',
		marginBottom: '1rem',
	},
	resetButton: {
		//margin: 'auto !important',
		margin: '0 3px 3px 0',
		display: 'block !important',
		justifyContent: 'center',
		width: '250px',
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

	const downloadFile = () => {
		const jsonContent = JSON.stringify(data, null, 2);
		const blob = new Blob([jsonContent], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'actionfile.json';
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};


  const [data, setData] = useState<any>(null);

  const apiUrl = '/actions';

  useEffect(() => {
    const retrieveFile = async () => {
      try {
        const response = await fetch(apiUrl);

        if (!response.ok) {
          throw new Error(
            `HTTP error! Status: ${response.status}`
          );
        }

        const af = await response.text();
        // Set the retrieved data in the state
        setData(JSON.parse(af as string));
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };
    // Call the fetchData function when the component mounts
    retrieveFile();
  }, []);

  const writeFile = async () => {
    try {
      const response = await fetch('/', {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
          "Content-type": "application/json; charset=UTF-8"
        }
      });

        if (!response.ok) {
          throw new Error(
            `HTTP error! Status: ${response.status}`
          );
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };

  //

	const classes = useStyles();
	const stringifiedData = useMemo(
		() => JSON.stringify(data, null, 2),
		[data]
	);

	return (
		<Fragment>
			<h1 className={classes.title}>RedemptionCore Action Editor</h1>

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
          <div style={{ margin: '8px 0' }}>
						<Button
							className={classes.resetButton}
							onClick={writeFile}
							color='primary'
							variant='contained'
						>
							save to rpi
            </Button>

						<input type='file' accept='.json' onChange={handleFileUpload} style={{ display: 'none' }} id='fileInput'/>
						<label htmlFor='fileInput'>
							<Button
								className={classes.resetButton}
								color='primary'
								variant='contained'
							>
								custom upload
							</Button>
						</label>

						<Button
							className={classes.resetButton}
							onClick={downloadFile}
							color='primary'
							variant='contained'
						>
							custom save
						</Button>

					</div>

					<div className={classes.dataContent}>
						<pre id='boundData' style={{ fontStyle: 'italic' }}>
							{stringifiedData}
						</pre>
					</div>
				</Grid>
			</Grid>
		</Fragment>
	);
};

export default App;
